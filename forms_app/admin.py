from django.contrib import admin
from django.db.models import JSONField
from django.forms import Textarea
from simple_history.admin import SimpleHistoryAdmin
from .models import FormTemplate, FormInstance

JSON_OVERRIDES = {JSONField: {'widget': Textarea(attrs={'rows': 12, 'cols': 120})}}

@admin.register(FormTemplate)
class FormTemplateAdmin(SimpleHistoryAdmin):
    formfield_overrides = JSON_OVERRIDES
    list_display = ("id", "key", "version")
    search_fields = ("key", "version")
    list_filter = ("key", "version")
    ordering = ("key", "version")

@admin.register(FormInstance)
class FormInstanceAdmin(SimpleHistoryAdmin):
    formfield_overrides = JSON_OVERRIDES
    list_display = ("id", "subject", "template", "status", "updated_by")
    list_filter = ("status", "template")
    search_fields = ("subject__code", "subject__name")
    autocomplete_fields = ("subject", "template", "updated_by")
    ordering = ("-id",)
