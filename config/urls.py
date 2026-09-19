"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.tasks.views import TaskListCreateView
from apps.comments.views import CommentListCreateView
from apps.activities.views import ProjectActivityListView, TaskActivityListView

urlpatterns = [
    path('admin/', admin.site.urls),

    # OpenAPI Schema & Interactive Documentation
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/v1/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/v1/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API Resource Endpoints
    path('api/v1/auth/', include('apps.accounts.urls.auth_urls')),
    path('api/v1/teams/', include('apps.teams.urls.team_urls')),
    path('api/v1/projects/', include('apps.projects.urls.project_urls')),
    path('api/v1/projects/<int:project_id>/tasks/', TaskListCreateView.as_view(), name='project-tasks-list-create'),
    path('api/v1/projects/<int:project_id>/activities/', ProjectActivityListView.as_view(), name='project-activities-list'),
    path('api/v1/tasks/', include('apps.tasks.urls.task_urls')),
    path('api/v1/tasks/<int:task_id>/comments/', CommentListCreateView.as_view(), name='task-comments-list-create'),
    path('api/v1/tasks/<int:task_id>/activities/', TaskActivityListView.as_view(), name='task-activities-list'),
    path('api/v1/comments/', include('apps.comments.urls.comment_urls')),
]







