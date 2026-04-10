import logging

from rest_framework import serializers

from .models import Note

logger = logging.getLogger(__name__)


class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = (
            'id',
            'course',
            'title',
            'content',
            'is_pinned',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, attrs):
        request = self.context['request']
        user = request.user
        course = attrs.get('course', getattr(self.instance, 'course', None))

        if course is None:
            raise serializers.ValidationError({'course': 'Course is required.'})

        if user.is_instructor:
            if course.instructor_id != user.id:
                raise serializers.ValidationError('Instructors can only write notes on their own courses.')
            return attrs

        from apps.enrollments.models import Enrollment

        if not Enrollment.objects.filter(student=user, course=course).exists():
            raise serializers.ValidationError('You must be enrolled in this course to take notes.')

        logger.debug('Validated note request for user=%s course_id=%s', user.email, course.id)
        return attrs
