from django.urls import path
from .views import EnrollView, MyCoursesView, CourseProgressView, CompleteLessonView

urlpatterns = [
    path('courses/<int:course_id>/enroll/', EnrollView.as_view(), name='enroll'),
    path('courses/<int:course_id>/progress/', CourseProgressView.as_view(), name='course-progress'),
    path('lessons/<int:lesson_id>/complete/', CompleteLessonView.as_view(), name='complete-lesson'),
    path('my-courses/', MyCoursesView.as_view(), name='my-courses'),
]

