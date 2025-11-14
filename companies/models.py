from django.db import models
from django.conf import settings


class Company(models.Model): #seccion 4 ficha api
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    management_address = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    employees_count = models.PositiveIntegerField(default=0)
    sector = models.CharField(max_length=100)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class ProblemStatement(models.Model):  # ficha proyecto api problemática con contraparte
    problem_to_address = models.TextField(blank=True, default="")
    why_important = models.TextField(blank=True, default="")
    stakeholders = models.TextField(blank=True, default="")
    related_area = models.TextField(blank=True, default="")
    benefits_short_medium_long_term = models.TextField(blank=True, default="")
    problem_definition = models.TextField(blank=True, default="")
    subject = models.ForeignKey('subjects.Subject', on_delete=models.CASCADE, related_name='problem_statements')
    company = models.ForeignKey('companies.Company', on_delete=models.PROTECT, related_name='problem_statements')

    class Meta:
        ordering = ("subject", "company")

    def __str__(self):
        return f"Problem statement: {self.subject.code} - {self.company.name}"


class CounterpartContact(models.Model): #ficha proyecto api ¿Quiénes participarán de la identificación de la problemática? 
    problem_statement = models.ForeignKey('companies.ProblemStatement', on_delete=models.CASCADE, related_name='counterpart_contacts')
    name = models.CharField(max_length=255, blank=True, default="")
    counterpart_area = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ("problem_statement", "id")

    def __str__(self):
        return f"Contact {self.name} - {self.problem_statement_id}"


class CompanyEngagementScope(models.Model):  # alcance con contraparte, movido desde subjects
    benefits_from_student = models.TextField(blank=True, default="")
    has_value_or_research_project = models.BooleanField(default=False)
    time_availability_and_participation = models.TextField(blank=True, default="")
    workplace_has_conditions_for_group = models.BooleanField(default=False)
    meeting_schedule_availability = models.TextField(blank=True, default="")
    # Asociacion con Subject sin FK: guardar code y section
    subject_code = models.CharField(max_length=20)
    subject_section = models.CharField(max_length=10, default="1")
    # Dependencia con Company
    company = models.ForeignKey('companies.Company', on_delete=models.PROTECT, related_name='engagement_scopes')

    class Meta:
        ordering = ("company", "subject_code", "subject_section")
        constraints = [
            models.UniqueConstraint(fields=("company", "subject_code", "subject_section"), name="uniq_company_engagement_company_subject"),
        ]

    def __str__(self):
        return f"Engagement scope for {self.subject_code} - {self.company.name}"
