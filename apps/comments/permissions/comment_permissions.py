from rest_framework import permissions


class IsCommentAuthor(permissions.BasePermission):
    """
    Object-level permission checking if user is the author of the comment.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False
        return obj.author_id == request.user.id


class IsCommentAuthorOrReporter(permissions.BasePermission):
    """
    Object-level permission checking if user is author of comment OR project reporter.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        if obj.author_id == request.user.id:
            return True

        return obj.task.project.reporter_id == request.user.id
