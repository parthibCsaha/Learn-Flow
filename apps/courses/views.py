from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
 
from .models import Category, Course, Section, Lesson
from .serializers import (
    CategorySerializer,
    CourseListSerializer,
    CourseDetailSerializer,
    CourseWriteSerializer,
    SectionSerializer,
    LessonSerializer,
)
from .permissions import IsInstructor, IsCourseOwner
from .filters import CourseFilter

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
        if self.action in ('create', 'update', 'partial_update'):
            return CourseWriteSerializer
        if self.action == 'retrieve':
            return CourseDetailSerializer
        return CourseListSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.IsAuthenticated(), IsInstructor()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsCourseOwner()]
        return [permissions.IsAuthenticated()]
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsCourseOwner])
    def publish(self, request, pk=None):
        """Toggle course publish state."""
        course = self.get_object()
        course.is_published = not course.is_published
        course.save(update_fields=['is_published'])
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

        