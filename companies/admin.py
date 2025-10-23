from django.contrib import admin
from .models import Company


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sector", "employees_count", "api_type", "email", "phone")
    list_filter = ("api_type", "sector")
    search_fields = ("name", "email", "phone")
    ordering = ("name",)
