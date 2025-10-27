
# Create your models here.
from django.db import models
from django.conf import settings
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
    code = models.CharField(max_length=20, unique=True) #olbigatorio
    name = models.CharField(max_length=200) #olbigatorio
    campus = models.CharField(max_length=50, default="chillan")
    hours = models.PositiveIntegerField(default=0)
    api_type = models.PositiveSmallIntegerField(
        default=1,
        choices=((1, "Type 1"), (2, "Type 2"), (3, "Type 3")),
    )
    # normalized: units, technical_competencies and company_boundary_conditions moved to dedicated tables
    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='subjects',
        null=True,
        blank=True,
    )
    area = models.ForeignKey('subjects.Area', on_delete=models.PROTECT, related_name='subjects') #olbigatorio
    semester = models.ForeignKey('subjects.SemesterLevel', on_delete=models.PROTECT, related_name='subjects') #olbigatorio

    def __str__(self):
        return f"{self.code} - {self.name}"


class SubjectUnit(models.Model):  #ficha proyecto api unidades
    number = models.IntegerField()
    expected_learning = models.TextField(blank=True, null=True)
    unit_hours = models.PositiveIntegerField(blank=True, null=True)
    activities_description = models.TextField(blank=True, null=True)
    evaluation_evidence = models.TextField(blank=True, null=True)
    evidence_detail = models.TextField(blank=True, null=True)
    counterpart_link = models.TextField(blank=True, null=True)
    place_mode_type = models.TextField(blank=True, null=True)
    counterpart_participant_name = models.TextField(blank=True, null=True)
    subject = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='units')

    class Meta:
        ordering = ("subject", "number")
        constraints = [
            models.CheckConstraint(
                check=models.Q(number__gte=1) & models.Q(number__lte=4),
                name="unit_number_between_1_4",
            ),
            models.UniqueConstraint(fields=("subject", "number"), name="uniq_unit_subject_number"),
        ]

    def __str__(self):
        return f"Unit {self.number} - {self.subject.code}"


class SubjectTechnicalCompetency(models.Model): #ficha proyecto api competencias técnicas
    number = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    subject = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='technical_competencies')

    class Meta:
        ordering = ("subject", "number")
        constraints = [
            models.CheckConstraint(
                check=models.Q(number__gte=1) & models.Q(number__lte=5),
                name="competency_number_between_1_5",
            ),
            models.UniqueConstraint(fields=("subject", "number"), name="uniq_competency_subject_number"),
        ]

    def __str__(self):
        return f"Competency {self.number} - {self.subject.code}"


class CompanyBoundaryCondition(models.Model):
    large_company = models.BooleanField(null=True)
    medium_company = models.BooleanField(null=True)
    small_company = models.BooleanField(null=True)
    family_enterprise = models.BooleanField(null=True)
    not_relevant = models.BooleanField(null=True)
    company_type_description = models.TextField(blank=True, null=True)
    company_requirements_for_level_2_3 = models.TextField(blank=True, null=True)
    project_minimum_elements = models.TextField(blank=True, null=True)
    subject = models.OneToOneField('subjects.Subject', on_delete=models.CASCADE, related_name='company_boundary_conditions')

    class Meta:
        ordering = ("subject",)

    def __str__(self):
        return f"Boundary conditions - {self.subject.code}"


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


class CompanyEngagementScope(models.Model): #ficha proyecto api alcance con contraparte
    benefits_from_student = models.TextField(blank=True, default="")
    has_value_or_research_project = models.BooleanField(default=False)
    time_availability_and_participation = models.TextField(blank=True, default="")
    workplace_has_conditions_for_group = models.BooleanField(default=False)
    meeting_schedule_availability = models.TextField(blank=True, default="")
    subject = models.OneToOneField('subjects.Subject', on_delete=models.CASCADE, related_name='engagement_scope')

    class Meta:
        ordering = ("subject",)

    def __str__(self):
        return f"Engagement scope for {self.subject.code}"


def default_counterpart_contacts(): # encargados contraparte (lista sin límite, default 1 vacío)
    return [
        {
            "name": "",
            "counterpart_area": "",
            "role": "",
        }
    ]


class ProblemStatement(models.Model): #ficha proyecto api problemática con contraparte
    problem_to_address = models.TextField(blank=True, default="")
    why_important = models.TextField(blank=True, default="")
    stakeholders = models.TextField(blank=True, default="")
    related_area = models.TextField(blank=True, default="")
    benefits_short_medium_long_term = models.TextField(blank=True, default="")
    problem_definition = models.TextField(blank=True, default="")
    counterpart_contacts = models.JSONField(default=default_counterpart_contacts)
    subject = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='problem_statements')
    company = models.ForeignKey('companies.Company', on_delete=models.PROTECT, related_name='problem_statements')

    class Meta:
        ordering = ("subject", "company")
        constraints = [
            models.UniqueConstraint(fields=["subject", "company"], name="uniq_problem_statement_subject_company"),
        ]

    def __str__(self):
        return f"Problem statement: {self.subject.code} - {self.company.name}"
