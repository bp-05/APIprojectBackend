from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError("El nombre de usuario es obligatorio")
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "ADMIN")  # ← garantiza rol ADMIN
        if extra_fields.get("is_staff") is not True or extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser debe tener is_staff=True e is_superuser=True")
        return self.create_user(username, email, password, **extra_fields)

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        VCM   = "VCM",   "Vinculación con el Medio"
        DA    = "DA",    "Dirección Académica"
        DOC   = "DOC",   "Docente"
        COORD = "COORD", "Coordinador API"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.DOC)
    objects = UserManager()

    class Meta:
        constraints = [
            # Si es superusuario, el rol debe ser ADMIN
            models.CheckConstraint(
                check=~models.Q(is_superuser=True) | models.Q(role="ADMIN"),
                name="superuser_must_be_admin_role"
            )
        ]

