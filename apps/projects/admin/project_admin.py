from django.contrib import admin
from apps.projects.models import Project, ProjectTeam


class ProjectTeamInline(admin.TabularInline):
    model = ProjectTeam
    extra = 1
    raw_id_fields = ('team',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('id', 'key', 'title', 'reporter', 'is_deleted', 'created_at', 'updated_at')
    search_fields = ('key', 'title', 'reporter__email')
    list_filter = ('is_deleted', 'created_at')
    inlines = [ProjectTeamInline]
