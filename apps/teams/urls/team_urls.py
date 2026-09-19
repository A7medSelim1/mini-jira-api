from django.urls import path
from apps.teams.views import (
    TeamListCreateView,
    TeamDetailView,
    TeamMembershipListCreateView,
    TeamMembershipDetailView,
)

urlpatterns = [
    path('', TeamListCreateView.as_view(), name='team-list-create'),
    path('<int:pk>/', TeamDetailView.as_view(), name='team-detail'),
    path('<int:pk>/members/', TeamMembershipListCreateView.as_view(), name='team-members-list-create'),
    path('<int:pk>/members/<int:user_id>/', TeamMembershipDetailView.as_view(), name='team-members-detail'),
]
