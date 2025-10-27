from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Subject,
    Area,
    SemesterLevel,
    SubjectUnit,
    SubjectTechnicalCompetency,
    CompanyBoundaryCondition,
    CompanyRequirement,
    Api3Alternance,
    ApiType2Completion,
    ApiType3Completion,
    CompanyEngagementScope,
    ProblemStatement,
)

@admin.register(Subject)
class SubjectAdmin(SimpleHistoryAdmin):
    list_display = ("id", "code", "name", "campus", "hours", "api_type", "teacher", "area", "semester")
    list_filter = ( "api_type", "area", "semester")
    search_fields = ("code", "name", "teacher__username", "teacher__first_name", "teacher__last_name")
    autocomplete_fields = ("teacher", "area", "semester")
    ordering = ("code",)


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(SemesterLevel)
class SemesterLevelAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("id",)


@admin.register(SubjectUnit)
class SubjectUnitAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "number", "unit_hours")
    list_filter = ("number",)
    search_fields = ("subject__code", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject", "number")


@admin.register(SubjectTechnicalCompetency)
class SubjectTechnicalCompetencyAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "number")
    list_filter = ("number",)
    search_fields = ("subject__code", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject", "number")


@admin.register(CompanyBoundaryCondition)
class CompanyBoundaryConditionAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "large_company", "medium_company", "small_company", "family_enterprise", "not_relevant")
    search_fields = ("subject__code", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject",)


@admin.register(CompanyRequirement)
class CompanyRequirementAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "company", "sector", "interaction_type", "worked_before", "can_receive_alternance", "alternance_students_quota")
    list_filter = ("interaction_type", "worked_before", "can_receive_alternance")
    search_fields = ("subject__code", "subject__name", "company__name")
    autocomplete_fields = ("subject", "company")
    ordering = ("subject",)


@admin.register(Api3Alternance)
class Api3AlternanceAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "student_role", "students_quota", "tutor_name", "tutor_email", "alternance_hours")
    search_fields = ("subject__code", "subject__name", "tutor_name", "tutor_email")
    autocomplete_fields = ("subject",)
    ordering = ("subject",)


@admin.register(ApiType2Completion)
class ApiType2CompletionAdmin(admin.ModelAdmin):
    list_display = ("id", "subject")
    search_fields = ("subject__code", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject",)


@admin.register(ApiType3Completion)
class ApiType3CompletionAdmin(admin.ModelAdmin):
    list_display = ("id", "subject")
    search_fields = ("subject__code", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject",)


@admin.register(CompanyEngagementScope)
class CompanyEngagementScopeAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "has_value_or_research_project", "workplace_has_conditions_for_group")
    search_fields = ("subject__code", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject",)


@admin.register(ProblemStatement)
class ProblemStatementAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "company")
    search_fields = ("subject__code", "subject__name", "company__name")
    autocomplete_fields = ("subject", "company")
    ordering = ("subject",)

