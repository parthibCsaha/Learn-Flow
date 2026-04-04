from rest_framework import serializers
from .models import Enrollment, LessonProgress
from apps.courses.serializers import CourseListSerializer


class EnrollmentSerializer(serializers.ModelSerializer):
    course = CourseListSerializer(read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)

    class Meta:
        model = Enrollment
        fields = ('id', 'course', 'enrolled_at', 'progress_percentage', 'is_completed')
        read_only_fields = ('enrolled_at',)


class LessonProgressSerializer(serializers.ModelSerializer):
    lesson_title = serializers.CharField(source='lesson.title', read_only=True)

    class Meta:
        model = LessonProgress
        fields = ('id', 'lesson', 'lesson_title', 'is_completed', 'completed_at')
        read_only_fields = ('completed_at',)


class CourseProgressSerializer(serializers.Serializer):
    """Summary of progress for a specific course."""
    course_id = serializers.IntegerField()
    course_title = serializers.CharField()
    total_lessons = serializers.IntegerField()
    completed_lessons = serializers.IntegerField()
    progress_percentage = serializers.FloatField()
    is_completed = serializers.BooleanField()
    lessons = LessonProgressSerializer(many=True)

    