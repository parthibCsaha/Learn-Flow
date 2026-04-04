from django.urls import path
from .views import ReviewListCreateView, ReviewDetailView

urlpatterns = [
    path('courses/<int:course_id>/reviews/', ReviewListCreateView.as_view(), name='course-reviews'),
    path('reviews/<int:pk>/', ReviewDetailView.as_view(), name='review-detail'),
]