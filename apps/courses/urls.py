from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers
from .views import CategoryViewSet, CourseViewSet, SectionViewSet, LessonViewSet
 
router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='category')
router.register('courses', CourseViewSet, basename='course')
 
courses_router = nested_routers.NestedDefaultRouter(router, 'courses', lookup='course')
courses_router.register('sections', SectionViewSet, basename='course-sections')
 
sections_router = nested_routers.NestedDefaultRouter(courses_router, 'sections', lookup='section')
sections_router.register('lessons', LessonViewSet, basename='section-lessons')
 
urlpatterns = [
    path('', include(router.urls)),
    path('', include(courses_router.urls)),
    path('', include(sections_router.urls)),
]
