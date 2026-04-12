import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
 
from .ai_service import GroqAPIError, chat_completion
from .models import Category, Course, Section, Lesson
from .serializers import (
    CategorySerializer,
    CourseListSerializer,
    CourseDetailSerializer,
    CourseWriteSerializer,
    SectionSerializer,
    LessonSerializer,
    LessonSummaryRequestSerializer,
    LessonChatRequestSerializer,
)
from .permissions import IsInstructor, IsCourseOwner
from .filters import CourseFilter

logger = logging.getLogger(__name__)

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve categories. Read-only for all authenticated users."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (permissions.IsAuthenticated,)


class CourseViewSet(viewsets.ModelViewSet):
    """
    Courses CRUD.
    - List/Retrieve: all authenticated users (only published, unless instructor viewing own)
    - Create: instructors only
    - Update/Delete: course owner only
    """
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_class = CourseFilter
    search_fields = ('title', 'description', 'instructor__username')
    ordering_fields = ('created_at', 'price', 'title')
    ordering = ('-created_at',)

    def get_queryset(self):
        user = self.request.user

        logger.debug('Fetching courses for user: %s', user.email)

        if user.is_instructor:
            # Instructors see all their own courses (published + drafts)
            return Course.objects.select_related('instructor', 'category').filter(
                instructor=user
            ) | Course.objects.select_related('instructor', 'category').filter(
                is_published=True
            ).exclude(instructor=user)
        # Students only see published courses
        return Course.objects.select_related('instructor', 'category').filter(is_published=True)
    
    def get_serializer_class(self):
        logger.debug('Getting serializer class for action: %s', self.action)
         
        if self.action in ('create', 'update', 'partial_update'):
            return CourseWriteSerializer
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseListSerializer
    
    def get_permissions(self):
        logger.debug('Getting permissions for action: %s', self.action)

        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsInstructor()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsCourseOwner()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsCourseOwner])
    def publish(self, request, pk=None):
        """Toggle course publish state."""
        logger.debug('Toggling publish state for course_id=%s by user=%s', pk, request.user.email)

        course = self.get_object()
        course.is_published = not course.is_published
        course.save(update_fields=['is_published'])

        logger.info('Course %s publish state changed to %s by user %s', course.title, course.is_published, request.user.email)

        state = 'published' if course.is_published else 'unpublished'
        return Response({'detail': f'Course {state} successfully.', 'is_published': course.is_published})
     
class SectionViewSet(viewsets.ModelViewSet):
    """
    Sections within a course.
    - List/Retrieve: enrolled students + course instructor
    - Create/Update/Delete: course owner only
    """
    serializer_class = SectionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        qs = Section.objects.filter(
            course_id=self.kwargs['course_pk']
        ).prefetch_related('lessons')

        if user.is_instructor:
            return qs.filter(course__instructor=user)

        return qs.filter(course__enrollments__student=user).distinct()
    
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsCourseOwner()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        course = Course.objects.get(pk=self.kwargs['course_pk'])
        # Check ownership manually since perform_create doesn't go through has_object_permission
        
        logger.debug('Attempting to create section for course_id=%s by user=%s', course.id, self.request.user.email)
        
        if course.instructor != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not own this course.')
        serializer.save(course=course)

class LessonViewSet(viewsets.ModelViewSet):
    """
    Lessons within a section.
    Only enrolled students or the course instructor can view lessons.
    """
    serializer_class = LessonSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        qs = Lesson.objects.filter(section_id=self.kwargs['section_pk'])

        if user.is_instructor:
            return qs.filter(section__course__instructor=user)

        return qs.filter(section__course__enrollments__student=user).distinct()
 
    def _get_section(self):
        return Section.objects.select_related('course').get(pk=self.kwargs['section_pk'])

    def get_serializer_class(self):
        if self.action == 'summary':
            return LessonSummaryRequestSerializer
        if self.action == 'chat':
            return LessonChatRequestSerializer
        return LessonSerializer
    
    def get_permissions(self):
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsCourseOwner()]
        return [permissions.IsAuthenticated()]
    
    def list(self, request, *args, **kwargs):
        section = self._get_section()
        user = request.user
        # Allow if instructor or enrolled student
        if not user.is_instructor:
            from apps.enrollments.models import Enrollment
            if not Enrollment.objects.filter(student=user, course=section.course).exists():
                return Response(
                    {'detail': 'You must be enrolled to access lessons.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        return super().list(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        section = self._get_section()
        if section.course.instructor != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not own this course.')
        serializer.save(section=section)

    @staticmethod
    def _truncate_text(text, limit=10000):
        if not text:
            return ''
        text = text.strip()
        if len(text) <= limit:
            return text
        return f'{text[:limit]}...'

    def _get_lesson_ai_context(self, lesson):
        transcript = self._truncate_text(lesson.transcript)
        content = self._truncate_text(lesson.content)

        if transcript and content:
            return f'Video transcript:\n{transcript}\n\nLesson notes/content:\n{content}'
        if transcript:
            return f'Video transcript:\n{transcript}'
        if content:
            return f'Lesson notes/content:\n{content}'
        return ''

    @action(detail=True, methods=['post'], url_path='summary')
    def summary(self, request, *args, **kwargs):
        lesson = self.get_object()
        course = lesson.section.course
        lesson_context = self._get_lesson_ai_context(lesson)

        if not lesson_context:
            return Response(
                {'detail': 'Lesson has no text content or transcript to summarize.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        messages = [
            {
                'role': 'system',
                'content': (
                    'You are an LMS tutor. Create concise study summaries from lesson content. '
                    'Use simple language and keep the response structured.'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'Course: {course.title}\n'
                    f'Lesson: {lesson.title}\n\n'
                    'Please provide:\n'
                    '1) A short summary (4-6 lines)\n'
                    '2) 3-6 key bullet points\n\n'
                    f'Lesson context:\n{lesson_context}'
                ),
            },
        ]

        try:
            ai_response = chat_completion(messages)
        except ImproperlyConfigured as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except GroqAPIError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(
            {
                'lesson_id': lesson.id,
                'course_id': course.id,
                'summary': ai_response,
                'model': settings.GROQ_MODEL,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='chat')
    def chat(self, request, *args, **kwargs):
        payload = self.get_serializer(data=request.data)
        payload.is_valid(raise_exception=True)

        lesson = self.get_object()
        course = lesson.section.course
        lesson_context = self._get_lesson_ai_context(lesson)

        if not lesson_context:
            return Response(
                {'detail': 'Lesson has no text content or transcript for chat context.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_message = payload.validated_data['message']
        messages = [
            {
                'role': 'system',
                'content': (
                    'You are an LMS lesson assistant. Answer based only on the provided lesson context. '
                    'If context is insufficient, say so clearly.'
                ),
            },
            {
                'role': 'user',
                'content': (
                    f'Course: {course.title}\n'
                    f'Lesson: {lesson.title}\n\n'
                    f'Lesson context:\n{lesson_context}\n\n'
                    f'Question: {user_message}'
                ),
            },
        ]

        try:
            ai_response = chat_completion(messages)
        except ImproperlyConfigured as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except GroqAPIError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response(
            {
                'lesson_id': lesson.id,
                'course_id': course.id,
                'reply': ai_response,
                'model': settings.GROQ_MODEL,
            },
            status=status.HTTP_200_OK,
        )

        