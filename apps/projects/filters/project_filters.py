import django_filters
from django.db.models import Q
from apps.projects.models import Project


class ProjectFilter(django_filters.FilterSet):
    """
    FilterSet for Project queries.
    """
    search = django_filters.CharFilter(method='filter_search')
    reporter = django_filters.NumberFilter(field_name='reporter_id')

    class Meta:
        model = Project
        fields = ['search', 'reporter']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        val = value.strip()
        return queryset.filter(
            Q(key__icontains=val) |
            Q(title__icontains=val) |
            Q(description__icontains=val)
        )
