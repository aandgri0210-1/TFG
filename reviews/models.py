from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Review(models.Model):
	service = models.ForeignKey('services.Service', on_delete=models.CASCADE, related_name='reviews')
	reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews')
	title = models.CharField(max_length=120, default='')
	rating = models.DecimalField(
		max_digits=2,
		decimal_places=1,
		validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
	)
	comment = models.TextField(default='')
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)
	is_deleted = models.BooleanField(default=False)

	class Meta:
		ordering = ['-created_at']
		constraints = [
			models.UniqueConstraint(fields=['service', 'reviewer'], name='unique_service_reviewer_review'),
		]

	def __str__(self):
		return f'{self.service} - {self.reviewer} ({self.rating}/5)'


class ReviewReport(models.Model):
	REASON_CHOICES = [
		('inappropriate', 'Contenido inapropiado'),
		('spam', 'Spam'),
		('offensive', 'Ofensivo'),
		('fraud', 'Fraude'),
		('other', 'Otro'),
	]

	review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='reports')
	reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='review_reports')
	reason = models.CharField(max_length=20, choices=REASON_CHOICES)
	description = models.TextField(blank=True, default='')
	created_at = models.DateTimeField(auto_now_add=True)
	is_resolved = models.BooleanField(default=False)
	resolved_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'Reporte de {self.reporter} - {self.review} ({self.get_reason_display()})'
