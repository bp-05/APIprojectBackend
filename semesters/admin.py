from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import Semester

@admin.register(Semester)
class SemesterAdmin(SimpleHistoryAdmin):
    list_display = ("id", "code", "starts_at", "ends_at")
    search_fields = ("code",)
    ordering = ("-starts_at",)

