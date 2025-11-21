from django.contrib import admin
from .models import Company, ProblemStatement, CounterpartContact


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "sector", "employees_count", "email", "phone")
    list_filter = ("sector",)
    search_fields = ("name", "email", "phone")
    ordering = ("name",)


@admin.register(ProblemStatement)
class ProblemStatementAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "company")
    search_fields = ("subject__code", "subject__name", "company__name")
    autocomplete_fields = ("subject", "company")
    ordering = ("subject",)


@admin.register(CounterpartContact)
class CounterpartContactAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "name", "rut", "phone", "email", "counterpart_area", "role")
    search_fields = ("company__name", "name", "rut", "phone", "email", "counterpart_area", "role")
    autocomplete_fields = ("company",)
    ordering = ("company", "id")



