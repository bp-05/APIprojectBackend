from django.contrib import admin
from django.db.models import JSONField
from django.forms import Textarea
from simple_history.admin import SimpleHistoryAdmin
from .models import DescriptorFile

JSON_OVERRIDES = {JSONField: {'widget': Textarea(attrs={'rows': 12, 'cols': 120})}}

@admin.register(DescriptorFile)
class DescriptorFileAdmin(SimpleHistoryAdmin):
    formfield_overrides = JSON_OVERRIDES
    list_display = ("id", "subject", "semester", "processed_at", "is_scanned")
    list_filter = ("semester", "is_scanned")
    search_fields = ("subject__code", "subject__name")
    autocomplete_fields = ("subject", "semester")
    readonly_fields = ("text_cache", "meta", "processed_at")
    ordering = ("-processed_at", "-id")
