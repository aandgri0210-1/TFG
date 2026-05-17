from django.conf import settings
from django.db import models


class ServiceRequest(models.Model):
	class Status(models.TextChoices):
		PENDING = 'pending', 'Pendiente'
		ACCEPTED = 'accepted', 'Aceptada'
		CANCELLED = 'cancelled', 'Cancelada'
		COMPLETED = 'completed', 'Completada'

	customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_requests')
	service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='service_requests')
	message = models.TextField(blank=True)
	desired_date = models.DateField(null=True, blank=True)
	status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
	cancellation_reason = models.TextField(blank=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'{self.customer} - {self.service} ({self.get_status_display()})'

	@property
	def can_cancel(self):
		return self.status in {self.Status.PENDING, self.Status.ACCEPTED}
