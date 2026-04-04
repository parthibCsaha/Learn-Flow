from django.contrib import admin
from .models import Category, Course, Section, Lesson


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


class SectionInline(admin.TabularInline):
    model = Section
    extra = 0


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'instructor', 'category', 'price', 'is_published', 'created_at')
    list_filter = ('is_published', 'category')
    search_fields = ('title', 'instructor__email')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [SectionInline]


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'section', 'order', 'duration_minutes')


    