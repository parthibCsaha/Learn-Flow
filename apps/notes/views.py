import logging

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import Note
from .serializers import NoteSerializer

logger = logging.getLogger(__name__)


class NoteViewSet(viewsets.ModelViewSet):
    serializer_class = NoteSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, SearchFilter, OrderingFilter)
    filterset_fields = ('course', 'is_pinned')
    search_fields = ('title', 'content')
    ordering_fields = ('created_at', 'updated_at')
    ordering = ('-is_pinned', '-updated_at')

    def get_queryset(self):
        user = self.request.user
        queryset = Note.objects.filter(user=user).select_related('course')

        course_id = self.request.query_params.get('course')
        if course_id:
            queryset = queryset.filter(course_id=course_id)

        return queryset

    def perform_create(self, serializer):
        note = serializer.save(user=self.request.user)
        logger.info('Note created: note_id=%s user=%s course_id=%s', note.id, self.request.user.email, note.course_id)
