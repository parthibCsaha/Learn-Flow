from rest_framework.permissions import BasePermission, SAFE_METHODS
import logging

logger = logging.getLogger(__name__)


class IsInstructor(BasePermission):
    """Only instructors can access."""
    message = 'Access denied. You must be an instructor to perform this action.'
 
    def has_permission(self, request, view):
        logger.debug('Checking if user is instructor: %s', request.user.email)
        
        return request.user.is_authenticated and request.user.is_instructor
    

class IsInstructorOrReadOnly(BasePermission):
    """Instructors can write. Anyone authenticated can read."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.is_instructor
    

 
class IsCourseOwner(BasePermission):
    """Only the course instructor can modify."""
    message = 'You do not own this course.'
 
    def has_object_permission(self, request, view, obj):
        # obj could be Course, Section or Lesson
        if hasattr(obj, 'instructor'):
            return obj.instructor == request.user
        if hasattr(obj, 'course'):
            return obj.course.instructor == request.user
        if hasattr(obj, 'section'):
            return obj.section.course.instructor == request.user
        return False