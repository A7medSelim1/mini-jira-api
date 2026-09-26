from django.urls import path
from apps.tasks.views import (
    TaskListCreateView,
    GlobalTaskListView,
    TaskDetailView,
    TaskTransitionView,
    TaskAssignView,
)

urlpatterns = [
    path('projects/<int:project_id>/tasks/', TaskListCreateView.as_view(), name='project-tasks-list-create'),
    path('tasks/', GlobalTaskListView.as_view(), name='global-task-list'),
    path('tasks/<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:pk>/transition/', TaskTransitionView.as_view(), name='task-transition'),
    path('tasks/<int:pk>/assign/', TaskAssignView.as_view(), name='task-assign'),
]

