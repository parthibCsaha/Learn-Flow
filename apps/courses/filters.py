import django_filters
from .models import Course


class CourseFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
    is_free = django_filters.BooleanFilter(method='filter_free')

    class Meta:
        model = Course
        fields = ('category', 'min_price', 'max_price', 'is_free')

    def filter_free(self, queryset, name, value):
        if value:
            return queryset.filter(price=0)
        return queryset.exclude(price=0)
    

