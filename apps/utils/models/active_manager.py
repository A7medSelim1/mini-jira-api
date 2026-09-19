from django.db import models


class ActiveQuerySet(models.QuerySet):
    """
    Custom QuerySet for models supporting soft deletion.
    """
    def active(self):
        return self.filter(is_deleted=False)

    def deleted(self):
        return self.filter(is_deleted=True)


class ActiveManager(models.Manager):
    """
    Custom Manager that filters out soft-deleted records by default.
    Exposes `.all_with_deleted()` and `.deleted_only()` for internal/admin access.
    """
    def get_queryset(self):
        return ActiveQuerySet(self.model, using=self._db).active()

    def all_with_deleted(self):
        return ActiveQuerySet(self.model, using=self._db)

    def deleted_only(self):
        return ActiveQuerySet(self.model, using=self._db).deleted()
