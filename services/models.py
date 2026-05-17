from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils.text import slugify


class Category(models.Model):
	name = models.CharField(max_length=120, unique=True)
	slug = models.SlugField(max_length=140, unique=True)
	description = models.TextField(blank=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class ListingType(models.Model):
	name = models.CharField(max_length=80, unique=True)
	slug = models.SlugField(max_length=100, unique=True)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['name']

	def __str__(self):
		return self.name


class Service(models.Model):
	professional = models.ForeignKey(
		settings.AUTH_USER_MODEL,
		on_delete=models.CASCADE,
		related_name='services',
	)
	category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='services')
	listing_type = models.CharField(max_length=80, default='Servicio')
	title = models.CharField(max_length=160)
	slug = models.SlugField(max_length=180, unique=True)
	image = models.ImageField(
		upload_to='services/',
		blank=True,
		null=True,
		validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'webp'])],
	)
	description = models.TextField()
	city = models.CharField(max_length=120)
	location_place_id = models.CharField(max_length=255, blank=True)
	address = models.CharField(max_length=255, blank=True, default='')
	price_from = models.DecimalField(max_digits=10, decimal_places=2)
	cilindrada = models.PositiveIntegerField(null=True, blank=True)
	kilometros = models.PositiveIntegerField(null=True, blank=True)
	year = models.PositiveSmallIntegerField(null=True, blank=True)
	latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
	is_active = models.BooleanField(default=True)
	created_at = models.DateTimeField(auto_now_add=True)
	updated_at = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ['-created_at']

	def save(self, *args, **kwargs):
		if not self.slug:
			base_slug = slugify(self.title)
			slug = base_slug
			counter = 1
			while Service.objects.filter(slug=slug).exclude(pk=self.pk).exists():
				slug = f'{base_slug}-{counter}'
				counter += 1
			self.slug = slug
		super().save(*args, **kwargs)

	def __str__(self):
		return self.title


	@property
	def average_rating(self):
		aggregate = self.reviews.filter(is_deleted=False).aggregate(avg=models.Avg('rating'))
		return aggregate['avg'] or 0

	@property
	def review_count(self):
		return self.reviews.filter(is_deleted=False).count()

	def get_listing_type_display(self):
		value = (self.listing_type or '').strip()
		mapping = {
			'product': 'Producto',
			'service': 'Servicio',
		}
		return mapping.get(value.lower(), value)

	@property
	def images(self):
		"""Return all images for this service, with fallback to legacy image field"""
		service_images = self.service_images.all()
		if service_images.exists():
			return service_images
		elif self.image:
			# Return a queryset-like object for compatibility
			return [self.image]
		return []

	def has_multiple_images(self):
		"""Check if service has multiple images"""
		return self.service_images.count() > 1

	def get_cover_image(self):
		"""Get the cover/first image"""
		service_img = self.service_images.first()
		if service_img:
			return service_img.image
		return self.image


class ServiceReport(models.Model):
	REASON_CHOICES = [
		('inappropriate', 'Contenido inapropiado'),
		('spam', 'Spam'),
		('offensive', 'Ofensivo'),
		('fraud', 'Fraude'),
		('other', 'Otro'),
	]

	service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='reports')
	reporter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='service_reports')
	reason = models.CharField(max_length=20, choices=REASON_CHOICES)
	description = models.TextField(blank=True, default='')
	created_at = models.DateTimeField(auto_now_add=True)
	is_resolved = models.BooleanField(default=False)
	resolved_at = models.DateTimeField(null=True, blank=True)

	class Meta:
		ordering = ['-created_at']

	def __str__(self):
		return f'Reporte de {self.reporter} - {self.service} ({self.get_reason_display()})'



class ServiceImage(models.Model):
	service = models.ForeignKey(
		Service,
		on_delete=models.CASCADE,
		related_name='service_images',
	)
	image = models.ImageField(
		upload_to='services/',
		validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'webp'])],
	)
	order = models.PositiveIntegerField(default=0)
	created_at = models.DateTimeField(auto_now_add=True)

	class Meta:
		ordering = ['order', 'created_at']
		unique_together = ('service', 'order')

	def __str__(self):
		return f"{self.service.title} - Image {self.order}"
