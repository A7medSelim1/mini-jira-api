from django.urls import path
from apps.projects.views import (
    ProjectListCreateView,
    ProjectDetailView,
    ProjectTeamsListCreateView,
    ProjectTeamsDetailView,
)

urlpatterns = [
    path('', ProjectListCreateView.as_view(), name='project-list-create'),
    path('<int:pk>/', ProjectDetailView.as_view(), name='project-detail'),
    path('<int:pk>/teams/', ProjectTeamsListCreateView.as_view(), name='project-teams-list-create'),
    path('<int:pk>/teams/<int:team_id>/', ProjectTeamsDetailView.as_view(), name='project-teams-detail'),
]
