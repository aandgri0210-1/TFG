from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
	class Role(models.TextChoices):
		CUSTOMER = 'customer', 'Cliente'
		PROFESSIONAL = 'professional', 'Profesional'
		ADMIN = 'admin', 'Administrador'

	email = models.EmailField(unique=True)
	role = models.CharField(max_length=20, choices=Role.choices, default=Role.CUSTOMER)
	must_change_password = models.BooleanField(default=False)

	def __str__(self):
		return self.get_full_name() or self.username

	@property
	def is_professional_account(self):
		return self.role == self.Role.PROFESSIONAL

	@property
	def es_profesional(self):
		return self.role == self.Role.PROFESSIONAL

	@property
	def is_admin_account(self):
		return self.role == self.Role.ADMIN or self.is_superuser

	@property
	def es_admin(self):
		return self.is_admin_account


class Profile(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
	phone = models.CharField(max_length=30, blank=True)
	city = models.CharField(max_length=120, blank=True)
	address = models.CharField(max_length=255, blank=True)
	bio = models.TextField(blank=True)
	avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
	avatar_url = models.URLField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	def __str__(self):
		return f'Perfil de {self.user}'
