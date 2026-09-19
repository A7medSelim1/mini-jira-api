from django.contrib import admin
from apps.teams.models import Team, TeamMembership


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 1
    raw_id_fields = ('user',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_by', 'created_at', 'updated_at')
    search_fields = ('name', 'description', 'created_by__email')
    list_filter = ('created_at',)
    inlines = [TeamMembershipInline]
