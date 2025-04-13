from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from .managers import CustomUserManager
from django.db.models.signals import pre_delete
from django.contrib.auth.models import Group as OriginalGroup
from django.dispatch import receiver
import uuid

username_validator = UnicodeUsernameValidator()

# Create your models here.
class User(AbstractUser):
    class Roles(models.TextChoices):
        PROFESOR = 'profesor', 'Profesor'
        DIRECTOR = 'director', 'Director'
        ESTUDIANTE = 'estudiante', 'Estudiante'
        USUARIO_NORMAL = 'usuario_normal', 'Usuario normal'


    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField(unique=True)
    rol_usuario = models.CharField(
        max_length=20,
        choices=Roles.choices,
        default=Roles.USUARIO_NORMAL
    )
    username = models.CharField(
        "username",
        max_length=150,
        help_text="Requerido. 150 caracteres o menos. Solo letras, dígitos y @/./+/-/_",
        validators=[username_validator],
        error_messages={
            "unique": "Ya existe un usuario con ese nombre de usuario.",
        },
    )

    groups = models.ManyToManyField(
        OriginalGroup,
        related_name='custom_user_groups',
        blank=True
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomUserManager()

    @property
    def nombre_completo(self):
        try:
            return self.nombre_completo
        except:
            return self.email

    def __str__(self):
        return self.nombre_completo

    @staticmethod
    @receiver(pre_delete, sender='users.User')
    def safe_delete_usuario(sender, instance, **kwargs):
        instance.safe_delete = True
        instance.save()

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

        constraints = [
            models.UniqueConstraint(
                fields=['username', 'email'],
                name='unique_username_email'
            )
        ]


class Group(OriginalGroup):
    class Meta:
        proxy = True
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"