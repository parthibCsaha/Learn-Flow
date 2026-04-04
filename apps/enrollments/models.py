from django.db import models
from django.conf import settings
 
 
class Enrollment(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    enrolled_at = models.DateTimeField(auto_now_add=True)
 
    class Meta:
        db_table = 'enrollments'
        unique_together = ('student', 'course')

    def __str__(self):
        return f'{self.student.email} → {self.course.title}'
 
    @property
    def progress_percentage(self):
        total = self.course.total_lessons
        if total == 0:
            return 0
        completed = LessonProgress.objects.filter(
            enrollment=self,
            is_completed=True
        ).count()
        return round((completed / total) * 100, 1)
    
    @property
    def is_completed(self):
        return self.progress_percentage == 100.0
    
class LessonProgress(models.Model):
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name='lesson_progresses'
    )
    lesson = models.ForeignKey(
        'courses.Lesson',
        on_delete=models.CASCADE,
        related_name='progresses'
    )
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
 
    class Meta:
        db_table = 'lesson_progress'
        unique_together = ('enrollment', 'lesson')
 
    def __str__(self):
        return f'{self.enrollment.student.email} - {self.lesson.title}'