
# Create your models here.
from django.db import models
from django.conf import settings


def default_subject_units(): #ficha proeycto api tabla unidades
    return [
        {
            "number": None,
            "expected_learning": None,
            "unit_hours": None,
            "activities_description": None,
            "evaluation_evidence": None,
            "evidence_detail": None,
            "counterpart_link": None,
            "place_mode_type": None,
            "counterpart_participant_name": None,
        }
        for _ in range(3)
    ]


def default_subject_competencies(): #ficha api competencias tecnicas
    return [
        {
            "number": i,
            "description": "",
        }
        for i in range(1, 6)
    ]

def default_company_boundary_conditions(): #seccion 1 ficha api condiciones de borde empresas
    return {
        "large_company": False,
        "medium_company": False,
        "small_company": False,
        "family_enterprise": False,
        "not_relevant": False,
        "company_type_description": "",
        "company_requirements_for_level_2_3": "",
        "project_minimum_elements": "",
    }
class CompanyRequirement(models.Model): #seccion 3 ficha api empresas/instituciones
    INTERACTION_CHOICES = (
        ("virtual", "Virtual"),
        ("onsite_company", "On-site at company"),
        ("onsite_inacap", "On-site at INACAP"),
    )

    sector = models.CharField(max_length=100)
    worked_before = models.BooleanField(default=False)
    interest_collaborate = models.BooleanField(default=False)
    can_develop_activities = models.BooleanField(default=False)
    willing_design_project = models.BooleanField(default=False)
    interaction_type = models.CharField(max_length=20, choices=INTERACTION_CHOICES, default="virtual")
    has_guide = models.BooleanField(default=False)
    can_receive_alternance = models.BooleanField(default=False)
    alternance_students_quota = models.PositiveIntegerField(default=0)
    subject = models.OneToOneField('subjects.Subject', on_delete=models.CASCADE, related_name='company_requirement')
    company = models.ForeignKey('companies.Company', on_delete=models.PROTECT, related_name='requirements')

    class Meta:
        ordering = ("subject",)

    def __str__(self):
        return f"Requirement for {self.subject.code}"


class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name

class SemesterLevel(models.Model):
    name = models.CharField(max_length=20, unique=True)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.name

class Subject(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=200)
    campus = models.CharField(max_length=50, default="chillan")
    hours = models.PositiveIntegerField(default=0)
    api_type = models.PositiveSmallIntegerField(
        default=1,
        choices=((1, "Type 1"), (2, "Type 2"), (3, "Type 3")),
    )
    units = models.JSONField(default=default_subject_units)
    technical_competencies = models.JSONField(default=default_subject_competencies)
    company_boundary_conditions = models.JSONField(default=default_company_boundary_conditions)
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='subjects',
        null=True,
        blank=True,
    )
    area = models.ForeignKey('subjects.Area', on_delete=models.PROTECT, related_name='subjects')
    semester = models.ForeignKey('subjects.SemesterLevel', on_delete=models.PROTECT, related_name='subjects')

    def __str__(self):
        return f"{self.code} - {self.name}"


class Api3Alternance(models.Model): #post seccion 4 ficha api
    student_role = models.CharField(max_length=200)
    students_quota = models.PositiveIntegerField(default=0)
    tutor_name = models.CharField(max_length=200)
    tutor_email = models.EmailField()
    alternance_hours = models.PositiveIntegerField(default=0)
    subject = models.OneToOneField('subjects.Subject', on_delete=models.CASCADE, related_name='alternance')

    class Meta:
        ordering = ("subject",)

    def __str__(self):
        return f"Alternance for {self.subject.code}"


class ApiType2Completion(models.Model): #seccion 2 ficha api
    project_goal_students = models.TextField(blank=True, default="")
    deliverables_at_end = models.TextField(blank=True, default="")
    company_expected_participation = models.TextField(blank=True, default="")
    other_activities = models.TextField(blank=True, default="")
    subject = models.OneToOneField('subjects.Subject', on_delete=models.CASCADE, related_name='api2_completion')

    class Meta:
        ordering = ("subject",)

    def __str__(self):
        return f"API2 completion for {self.subject.code}"


class ApiType3Completion(models.Model): #seccion 2 ficha api
    project_goal_students = models.TextField(blank=True, default="")
    deliverables_at_end = models.TextField(blank=True, default="")
    expected_student_role = models.TextField(blank=True, default="")
    other_activities = models.TextField(blank=True, default="")
    master_guide_expected_support = models.TextField(blank=True, default="")
    subject = models.OneToOneField('subjects.Subject', on_delete=models.CASCADE, related_name='api3_completion')

    class Meta:
        ordering = ("subject",)

    def __str__(self):
        return f"API3 completion for {self.subject.code}"

