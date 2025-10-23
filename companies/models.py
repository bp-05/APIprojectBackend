from django.db import models


class Company(models.Model): #seccion 4 ficha api
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    management_address = models.CharField(max_length=255, blank=True, default="")
    spys_responsible_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=50)
    employees_count = models.PositiveIntegerField(default=0)
    sector = models.CharField(max_length=100)
    api_type = models.PositiveSmallIntegerField(
        default=1,
        choices=((1, "Type 1"), (2, "Type 2"), (3, "Type 3")),
    )

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name
