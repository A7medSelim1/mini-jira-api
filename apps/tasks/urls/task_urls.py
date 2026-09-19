from django.urls import path
from apps.tasks.views import (
    GlobalTaskListView,
    TaskDetailView,
    TaskTransitionView,
    TaskAssignView,
)

urlpatterns = [
    path('', GlobalTaskListView.as_view(), name='global-task-list'),
    path('<int:pk>/', TaskDetailView.as_view(), name='task-detail'),
    path('<int:pk>/transition/', TaskTransitionView.as_view(), name='task-transition'),
    path('<int:pk>/assign/', TaskAssignView.as_view(), name='task-assign'),
]
