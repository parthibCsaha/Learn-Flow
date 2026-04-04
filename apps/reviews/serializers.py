from rest_framework import serializers
from .models import Review
from apps.users.serializers import PublicUserSerializer


class ReviewSerializer(serializers.ModelSerializer):
    student = PublicUserSerializer(read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'student', 'rating', 'comment', 'created_at', 'updated_at')
        read_only_fields = ('created_at', 'updated_at')

    def validate(self, attrs):
        request = self.context['request']
        course = self.context['course']
        user = request.user

        # Only enrolled students can review
        from apps.enrollments.models import Enrollment
        if not Enrollment.objects.filter(student=user, course=course).exists():
            raise serializers.ValidationError('You must be enrolled to review this course.')

        # One review per student per course (on create only)
        if self.instance is None:
            if Review.objects.filter(student=user, course=course).exists():
                raise serializers.ValidationError('You have already reviewed this course.')

        return attrs

    def create(self, validated_data):
        validated_data['student'] = self.context['request'].user
        validated_data['course'] = self.context['course']
        return super().create(validated_data)