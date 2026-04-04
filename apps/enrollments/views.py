from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Enrollment, LessonProgress
from .serializers import EnrollmentSerializer, CourseProgressSerializer, LessonProgressSerializer
from .tasks import send_enrollment_email, send_completion_email
from apps.courses.models import Course, Lesson


class EnrollView(APIView):
    """
    POST /api/courses/{course_id}/enroll/
    Enroll the authenticated student in a course.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, course_id):
        user = request.user

        if user.is_instructor:
            return Response(
                {'detail': 'Instructors cannot enroll in courses.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            course = Course.objects.get(pk=course_id, is_published=True)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found or not published.'}, status=status.HTTP_404_NOT_FOUND)

        if Enrollment.objects.filter(student=user, course=course).exists():
            return Response({'detail': 'You are already enrolled in this course.'}, status=status.HTTP_400_BAD_REQUEST)

        enrollment = Enrollment.objects.create(student=user, course=course)

        # Fire async email task
        send_enrollment_email.delay(user.id, course.id)

        return Response(
            {'detail': f'Successfully enrolled in "{course.title}".', 'enrollment_id': enrollment.id},
            status=status.HTTP_201_CREATED
        )


class MyCoursesView(generics.ListAPIView):
    """
    GET /api/my-courses/
    List all courses the authenticated student is enrolled in.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user
        ).select_related('course', 'course__instructor', 'course__category')


class CourseProgressView(APIView):
    """
    GET /api/courses/{course_id}/progress/
    Get the authenticated student's progress for a specific course.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, course_id):
        try:
            enrollment = Enrollment.objects.get(
                student=request.user,
                course_id=course_id
            )
        except Enrollment.DoesNotExist:
            return Response({'detail': 'You are not enrolled in this course.'}, status=status.HTTP_404_NOT_FOUND)

        course = enrollment.course
        total_lessons = course.total_lessons
        lesson_progresses = LessonProgress.objects.filter(enrollment=enrollment).select_related('lesson')
        completed_lessons = lesson_progresses.filter(is_completed=True).count()

        progress_percentage = round((completed_lessons / total_lessons) * 100, 1) if total_lessons > 0 else 0

        data = {
            'course_id': course.id,
            'course_title': course.title,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'progress_percentage': progress_percentage,
            'is_completed': progress_percentage == 100.0,
            'lessons': lesson_progresses,
        }

        serializer = CourseProgressSerializer(data)
        return Response(serializer.data)


class CompleteLessonView(APIView):
    """
    POST /api/lessons/{lesson_id}/complete/
    Mark a lesson as completed for the authenticated student.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, lesson_id):
        user = request.user

        try:
            lesson = Lesson.objects.select_related('section__course').get(pk=lesson_id)
        except Lesson.DoesNotExist:
            return Response({'detail': 'Lesson not found.'}, status=status.HTTP_404_NOT_FOUND)

        course = lesson.section.course

        try:
            enrollment = Enrollment.objects.get(student=user, course=course)
        except Enrollment.DoesNotExist:
            return Response({'detail': 'You are not enrolled in this course.'}, status=status.HTTP_403_FORBIDDEN)

        progress, created = LessonProgress.objects.get_or_create(
            enrollment=enrollment,
            lesson=lesson,
        )

        if progress.is_completed:
            return Response({'detail': 'Lesson already marked as completed.'}, status=status.HTTP_200_OK)

        progress.is_completed = True
        progress.completed_at = timezone.now()
        progress.save(update_fields=['is_completed', 'completed_at'])

        # Check if entire course is now complete
        if enrollment.is_completed:
            send_completion_email.delay(user.id, course.id)
            return Response({
                'detail': 'Lesson completed. Congratulations — you finished the course!',
                'course_completed': True,
            })

        return Response({
            'detail': 'Lesson marked as completed.',
            'course_completed': False,
            'progress_percentage': enrollment.progress_percentage,
        })