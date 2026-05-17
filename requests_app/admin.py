from django.contrib import admin

from .models import ServiceRequest


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
	list_display = ('service', 'customer', 'status', 'desired_date', 'created_at')
	list_filter = ('status', 'created_at')
	search_fields = ('service__title', 'customer__username', 'customer__email')
