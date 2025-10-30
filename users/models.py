from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser debe tener is_staff=True e is_superuser=True")
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        VCM = "VCM", "Vinculacion con el medio"
        DAC = "DAC", "Departamento Academico"
        DC = "DC", "Director de carrera"
        DOC = "DOC", "Docente"
        COORD = "COORD", "Coordinador API"

    # Usamos email como identificador y eliminamos username
    username = None
    email = models.EmailField("email address", unique=True)

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.DOC)
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        constraints = [
            # Si es superusuario, el rol debe ser ADMIN
            models.CheckConstraint(
                check=~models.Q(is_superuser=True) | models.Q(role="ADMIN"),
                name="superuser_must_be_admin_role",
            )
        ]

