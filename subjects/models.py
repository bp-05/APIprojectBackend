from django.db import models
from django.conf import settings

class InteractionType(models.Model):
    code = models.CharField(max_length=32, unique=True)
    label = models.CharField(max_length=64)

    class Meta:
        ordering = ("code",)

    def __str__(self):
        return self.label


class PossibleCounterpart(models.Model): # seccion 3 ficha api empresas/instituciones
    sector = models.CharField(max_length=100)
    worked_before = models.BooleanField(default=False)
    interest_collaborate = models.BooleanField(default=False)
    can_develop_activities = models.BooleanField(default=False)
    willing_design_project = models.BooleanField(default=False)
    interaction_types = models.ManyToManyField('subjects.InteractionType', related_name='possible_counterparts', blank=True)
    has_guide = models.BooleanField(default=False)
    can_receive_alternance = models.BooleanField(default=False)
    alternance_students_quota = models.PositiveIntegerField(default=0)
    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='possible_counterparts',
        null=True,
        blank=True,
    )
    company = models.ForeignKey('companies.Company', on_delete=models.PROTECT, related_name='possible_counterparts')

    class Meta:
        ordering = ("subject", "company")
        constraints = [
            models.UniqueConstraint(fields=("subject", "company"), name="uniq_possible_counterpart_subject_company"),
        ]

    def __str__(self):
        subject_label = self.subject.code if self.subject_id else "Unassigned"
        company_label = getattr(self.company, 'name', 'N/A')
        return f"Possible counterpart for {subject_label} - {company_label}"


class Area(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Career(models.Model):
    name = models.CharField(max_length=150, unique=True)
    area = models.ForeignKey('subjects.Area', on_delete=models.PROTECT, related_name='careers')

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
    code = models.CharField(max_length=20) #olbigatorio
    section = models.CharField(max_length=30, default="1")  # mandatory, text up to 30 chars
    name = models.CharField(max_length=200) #olbigatorio
    campus = models.CharField(max_length=50, default="chillan")
    # Jornada: diurna | vespertina
    shift = models.CharField(
        max_length=10,
        choices=(("diurna", "diurna"), ("vespertina", "vespertina")),
        default="diurna",
    )
    # Fase/estado manual de avance
    PHASE_CHOICES = (
        ("inicio", "Inicio"),
        ("formulacion", "Formulación de requerimientos"),
        ("gestion", "Gestión de requerimientos"),
        ("validacion", "Validación de requerimientos"),
        ("completado", "Completado"),
    )
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES, default="inicio")
    hours = models.PositiveIntegerField(default=0)
    api_type = models.PositiveSmallIntegerField(
        default=2,
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
    # Mantener vínculo directo a Area (para descriptores) y opcionalmente a Career
    area = models.ForeignKey('subjects.Area', on_delete=models.PROTECT, related_name='subjects')
    career = models.ForeignKey('subjects.Career', on_delete=models.PROTECT, related_name='subjects', null=True, blank=True)
    semester = models.ForeignKey('subjects.SemesterLevel', on_delete=models.PROTECT, related_name='subjects') #olbigatorio

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("code", "section"), name="uniq_subject_code_section"),
        ]

    def __str__(self):
        return f"{self.code} (Sec. {self.section}) - {self.name}"

    def save(self, *args, **kwargs):
        # Infer shift from subject code: if code contains 'V' (case-insensitive), it's vespertina; otherwise diurna.
        if self.code:
            self.shift = "vespertina" if "V" in self.code.upper() else "diurna"
        super().save(*args, **kwargs)


class SubjectPhaseSchedule(models.Model):
    PHASE_CHOICES = Subject.PHASE_CHOICES
    subject = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='phase_schedules')
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES)
    days_allocated = models.PositiveIntegerField(default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("subject", "phase")
        constraints = [
            models.UniqueConstraint(fields=("subject", "phase"), name="uniq_subject_phase_schedule"),
        ]

    def __str__(self):
        return f"{self.subject.code} - {self.phase} ({self.days_allocated}d)"

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


class SubjectTechnicalCompetency(models.Model): #ficha api competencias técnicas
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


class CompanyBoundaryCondition(models.Model):  #ficha api seccion 1
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
