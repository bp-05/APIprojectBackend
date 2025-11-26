from django.db import models
from django.conf import settings
from .utils import get_default_period_from_settings


PERIOD_SEASON_CHOICES = (
    ("O", "Otoño"),
    ("P", "Primavera"),
)


class PeriodSetting(models.Model):
    """
    Stores the current academic period (single row table editable from admin/front).
    """

    SINGLETON_PK = 1

    id = models.PositiveSmallIntegerField(primary_key=True, default=SINGLETON_PK, editable=False)
    period_season = models.CharField(max_length=1, choices=PERIOD_SEASON_CHOICES)
    period_year = models.PositiveIntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Periodo actual"
        verbose_name_plural = "Periodo actual"

    def __str__(self):
        return f"{self.period_season}-{self.period_year}"

    def save(self, *args, **kwargs):
        self.pk = self.SINGLETON_PK
        super().save(*args, **kwargs)

    @classmethod
    def get_active(cls):
        default_season, default_year = get_default_period_from_settings()
        defaults = {
            "period_season": default_season,
            "period_year": default_year,
        }
        obj, _ = cls.objects.get_or_create(pk=cls.SINGLETON_PK, defaults=defaults)
        return obj

def _default_period_year():
    return PeriodSetting.get_active().period_year


def _default_period_season():
    return PeriodSetting.get_active().period_season


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
    alternance_students_quota = models.PositiveIntegerField(null=True, blank=True)
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
            models.UniqueConstraint(
                fields=("subject", "company"), 
                name="uniq_possible_counterpart_subject_company",
                condition=models.Q(subject__isnull=False)
            ),
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
    campus = models.CharField(max_length=50, default="Chillán")
    # Jornada: diurna | vespertina
    shift = models.CharField(
        max_length=10,
        choices=(("diurna", "diurna"), ("vespertina", "vespertina")),
        default="diurna",
    )
    period_year = models.PositiveIntegerField(default=_default_period_year)
    period_season = models.CharField(max_length=1, choices=PERIOD_SEASON_CHOICES, default=_default_period_season)
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
    total_students = models.PositiveIntegerField(null=True, blank=True)
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
            models.UniqueConstraint(
                fields=("code", "section", "period_year", "period_season"),
                name="uniq_subject_code_section_period",
            ),
        ]

    def __str__(self):
        return f"{self.code} (Sec. {self.section}, {self.period_code}) - {self.name}"

    def save(self, *args, **kwargs):
        # Infer shift from subject code: if code contains 'V' (case-insensitive), it's vespertina; otherwise diurna.
        if self.code:
            self.shift = "vespertina" if "V" in self.code.upper() else "diurna"
        super().save(*args, **kwargs)

    @property
    def period_code(self) -> str:
        return f"{self.period_season}-{self.period_year}"

    def get_phase_schedule(self, phase=None):
        phase_key = phase or self.phase
        return PeriodPhaseSchedule.objects.filter(
            period_year=self.period_year,
            period_season=self.period_season,
            phase=phase_key,
        ).first()

    @property
    def phase_start_date(self):
        schedule = self.get_phase_schedule()
        return getattr(schedule, "start_date", None)

    @property
    def phase_end_date(self):
        schedule = self.get_phase_schedule()
        return getattr(schedule, "end_date", None)

    @property
    def process_start_date(self):
        if not self.pk:
            return None
        qs = PeriodPhaseSchedule.objects.filter(
            period_year=self.period_year,
            period_season=self.period_season,
        )
        return qs.aggregate(models.Min("start_date")).get("start_date__min")

    @property
    def process_end_date(self):
        if not self.pk:
            return None
        qs = PeriodPhaseSchedule.objects.filter(
            period_year=self.period_year,
            period_season=self.period_season,
        )
        return qs.aggregate(models.Max("end_date")).get("end_date__max")


class PeriodPhaseSchedule(models.Model):
    PHASE_CHOICES = Subject.PHASE_CHOICES
    period_year = models.PositiveIntegerField()
    period_season = models.CharField(max_length=1, choices=PERIOD_SEASON_CHOICES)
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ("period_year", "period_season", "phase")
        constraints = [
            models.UniqueConstraint(
                fields=("period_year", "period_season", "phase"),
                name="uniq_period_phase_schedule",
            ),
        ]

    def __str__(self):
        return f"{self.period_season}-{self.period_year} - {self.phase}"

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


class CompanyEngagementScope(models.Model):  # alcance con contraparte
    benefits_from_student = models.TextField(blank=True, default="")
    has_value_or_research_project = models.BooleanField(default=False)
    time_availability_and_participation = models.TextField(blank=True, default="")
    workplace_has_conditions_for_group = models.BooleanField(default=False)
    meeting_schedule_availability = models.TextField(blank=True, default="")
    # Asociación directa con Subject
    subject = models.OneToOneField('subjects.Subject', on_delete=models.CASCADE, related_name='engagement_scope')

    class Meta:
        ordering = ("subject",)

    def __str__(self):
        return f"Engagement scope for {self.subject.code}"


class SubjectPhaseProgress(models.Model):
    """
    Tracks the progress status of each phase for a subject (used in Gantt view).
    """
    PHASE_CHOICES = (
        ("formulacion", "Formulación de requerimientos"),
        ("gestion", "Gestión de requerimientos"),
        ("validacion", "Validación de requerimientos"),
    )
    STATUS_CHOICES = (
        ("nr", "No realizado"),
        ("ec", "En curso"),
        ("rz", "Realizado"),
    )

    subject = models.ForeignKey(
        'subjects.Subject',
        on_delete=models.CASCADE,
        related_name='phase_progress'
    )
    phase = models.CharField(max_length=20, choices=PHASE_CHOICES)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='nr')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='phase_progress_updates'
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        ordering = ("subject", "phase")
        verbose_name = "Progreso de fase"
        verbose_name_plural = "Progresos de fase"
        constraints = [
            models.UniqueConstraint(
                fields=("subject", "phase"),
                name="uniq_subject_phase_progress",
            ),
        ]

    def __str__(self):
        return f"{self.subject.code} - {self.get_phase_display()} - {self.get_status_display()}"
