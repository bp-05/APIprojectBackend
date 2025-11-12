from django.contrib import admin
from django import forms
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    Subject,
    Area,
    Career,
    SemesterLevel,
    SubjectUnit,
    SubjectTechnicalCompetency,
    CompanyBoundaryCondition,
    CompanyRequirement,
    Api3Alternance,
    ApiType2Completion,
    ApiType3Completion,
    SubjectPhaseSchedule,
)
## Admins for ProblemStatement and CounterpartContact moved to companies.admin

@admin.register(Subject)
class SubjectAdmin(SimpleHistoryAdmin):
    list_display = ("id", "code", "section", "name", "campus", "shift", "phase", "hours", "api_type", "teacher", "area", "career", "semester")
    list_filter = ( "api_type", "area", "career", "semester", "section", "shift", "phase")
    search_fields = ("code", "section", "name", "teacher__email", "teacher__first_name", "teacher__last_name")
    autocomplete_fields = ("teacher", "area", "career", "semester")
    ordering = ("code", "section")


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ("id", "name")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Career)
class CareerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "area")
    search_fields = ("name", "area__name")
    list_filter = ("area",)
    autocomplete_fields = ("area",)
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
    class CompanyRequirementAdminForm(forms.ModelForm):
        class Meta:
            model = CompanyRequirement
            fields = "__all__"
            widgets = {
                'interaction_types': forms.CheckboxSelectMultiple,
            }

    form = CompanyRequirementAdminForm

    def interaction_types_list(self, obj):
        return ", ".join(obj.interaction_types.values_list('code', flat=True))

    interaction_types_list.short_description = "interaction_type"

    list_display = ("id", "subject", "company", "sector", "interaction_types_list", "worked_before", "can_receive_alternance", "alternance_students_quota")
    list_filter = ("interaction_types", "worked_before", "can_receive_alternance")
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


@admin.register(SubjectPhaseSchedule)
class SubjectPhaseScheduleAdmin(admin.ModelAdmin):
    list_display = ("id", "subject", "phase", "days_allocated", "start_date", "end_date")
    list_filter = ("phase",)
    search_fields = ("subject__code", "subject__name")
    autocomplete_fields = ("subject",)
    ordering = ("subject", "phase")

## CompanyEngagementScope admin movido a companies.admin


## Admins for ProblemStatement and CounterpartContact moved to companies.admin

