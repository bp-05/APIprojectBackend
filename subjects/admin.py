from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Subject

@admin.register(Subject)
class SubjectAdmin(SimpleHistoryAdmin):
    list_display = ("id", "code", "name", "teacher", "api_flag")
    list_filter = ("api_flag",)
    search_fields = ("code", "name", "teacher__username", "teacher__first_name", "teacher__last_name")
    autocomplete_fields = ("teacher",)
    ordering = ("code",)
