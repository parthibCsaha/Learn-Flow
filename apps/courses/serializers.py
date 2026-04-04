from rest_framework import serializers
from .models import Category, Course, Section, Lesson
from apps.users.serializers import PublicUserSerializer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')
        read_only_fields = ('slug',)


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ('id', 'title', 'content', 'video_url', 'order', 'duration_minutes')
 

class SectionSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
 
    class Meta:
        model = Section
        fields = ('id', 'title', 'order', 'lessons')
 
class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing courses."""
    instructor = PublicUserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_enrollments = serializers.IntegerField(read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
 
    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'description', 'thumbnail',
            'price', 'is_published', 'instructor', 'category',
            'average_rating', 'total_enrollments', 'total_lessons',
            'created_at',
        )

class CourseDetailSerializer(serializers.ModelSerializer):
    """Full serializer with nested sections and lessons."""
    instructor = PublicUserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    sections = SectionSerializer(many=True, read_only=True)
    average_rating = serializers.FloatField(read_only=True)
    total_enrollments = serializers.IntegerField(read_only=True)
    total_lessons = serializers.IntegerField(read_only=True)
 
    class Meta:
        model = Course
        fields = (
            'id', 'title', 'slug', 'description', 'thumbnail',
            'price', 'is_published', 'instructor', 'category',
            'sections', 'average_rating', 'total_enrollments', 'total_lessons',
            'created_at', 'updated_at',
        )


class CourseWriteSerializer(serializers.ModelSerializer):
    """Used for creating/updating a course (instructor side)."""
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(),
        source='category',
        required=False,
        allow_null=True
    )
 
    class Meta:
        model = Course
        fields = ('title', 'description', 'thumbnail', 'price', 'category_id')
 
    def create(self, validated_data):
        validated_data['instructor'] = self.context['request'].user
        return super().create(validated_data)