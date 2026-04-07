import logging

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied

from .models import Review
from .serializers import ReviewSerializer
from apps.courses.models import Course

logger = logging.getLogger(__name__)

class ReviewListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/courses/{course_id}/reviews/ — List all reviews for a course
    POST /api/courses/{course_id}/reviews/ — Submit a review (enrolled students only)
    """
    serializer_class = ReviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_course(self):
        logger.debug('Fetching course for review: course_id=%s', self.kwargs['course_id'])
        
        try:
            return Course.objects.get(pk=self.kwargs['course_id'], is_published=True)
        except Course.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('Course not found.')

    def get_queryset(self):
        logger.debug('Fetching reviews for course_id=%s', self.kwargs['course_id'])
        
        return Review.objects.filter(
            course_id=self.kwargs['course_id']
        ).select_related('student')

    def get_serializer_context(self):
        logger.debug('Getting serializer context for course_id=%s', self.kwargs['course_id'])
        
        context = super().get_serializer_context()
        context['course'] = self.get_course()
        return context

    def create(self, request, *args, **kwargs):
        logger.debug('Review submission attempt: user=%s course_id=%s', request.user.email, self.kwargs['course_id'])
        
        if request.user.is_instructor:
            return Response(
                {'detail': 'Instructors cannot review courses.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, *args, **kwargs)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/PATCH/DELETE /api/reviews/{id}/
    Only the review author can edit or delete their review.
    """
    serializer_class = ReviewSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Review.objects.select_related('student', 'course')

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['course'] = self.get_object().course
        return context

    def check_object_permissions(self, request, obj):
        super().check_object_permissions(request, obj)
        if request.method not in ('GET',) and obj.student != request.user:
            raise PermissionDenied('You can only edit your own reviews.')