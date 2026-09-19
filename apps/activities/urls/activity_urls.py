from django.urls import path
from apps.activities.views import TaskActivityListView

urlpatterns = [
    path('<int:task_id>/activities/', TaskActivityListView.as_view(), name='task-activities-list'),
]
