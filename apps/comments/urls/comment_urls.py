from django.urls import path
from apps.comments.views import CommentDetailView

urlpatterns = [
    path('<int:pk>/', CommentDetailView.as_view(), name='comment-detail'),
]
