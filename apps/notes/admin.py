from django.contrib import admin

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'course', 'is_pinned', 'updated_at')
    list_filter = ('is_pinned', 'course')
    search_fields = ('user__email', 'course__title', 'title', 'content')
