from django.db import models
from django.conf import settings
from subjects.models import PERIOD_SEASON_CHOICES


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

    @property
    def counterpart_contacts(self):
        return self.company.counterpart_contacts.all()


class CounterpartContact(models.Model): #ficha proyecto api ¿Quiénes participarán de la identificación de la problemática?
    company = models.ForeignKey('companies.Company', on_delete=models.CASCADE, related_name='counterpart_contacts')
    name = models.CharField(max_length=255, blank=True, default="")
    rut = models.CharField(max_length=50, blank=True, default="")
    phone = models.CharField(max_length=50, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    counterpart_area = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ("company", "id")

    def __str__(self):
        return f"Contact {self.name} - {self.company_id}"



