import django_filters
from django.db.models import Q
from apps.tasks.models import Task, TaskStatus, TaskPriority


class TaskFilter(django_filters.FilterSet):
    """
    FilterSet for Task queries.
    Supports filtering by project, assignee, status, priority, date range, and text search.
    """
    project = django_filters.NumberFilter(field_name='project_id')
    assignee = django_filters.NumberFilter(field_name='assignee_id')
    status = django_filters.ChoiceFilter(choices=TaskStatus.choices)
    priority = django_filters.ChoiceFilter(choices=TaskPriority.choices)
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Task
        fields = ['project', 'assignee', 'status', 'priority', 'created_after', 'created_before', 'search']

    def filter_search(self, queryset, name, value):
        if not value:
            return queryset
        val = value.strip()
        return queryset.filter(
            Q(task_key__icontains=val) |
            Q(title__icontains=val) |
            Q(description__icontains=val)
        )
