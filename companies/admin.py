from django.contrib import admin
from .models import Company, ProblemStatement, CounterpartContact, CompanyEngagementScope


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
    list_display = ("id", "problem_statement", "name", "counterpart_area", "role")
    search_fields = ("problem_statement__subject__code", "problem_statement__subject__name", "name", "counterpart_area", "role")
    autocomplete_fields = ("problem_statement",)
    ordering = ("problem_statement", "id")


@admin.register(CompanyEngagementScope)
class CompanyEngagementScopeAdmin(admin.ModelAdmin):
    list_display = ("id", "company", "subject_code", "subject_section", "has_value_or_research_project", "workplace_has_conditions_for_group")
    list_filter = ("has_value_or_research_project", "workplace_has_conditions_for_group", "company")
    search_fields = ("company__name", "subject_code", "subject_section")
    autocomplete_fields = ("company",)
    ordering = ("company", "subject_code", "subject_section")
