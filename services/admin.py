from django.contrib import admin

from .models import Category, ListingType, Service


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	prepopulated_fields = {'slug': ('name',)}
	list_display = ('name', 'slug')
	search_fields = ('name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
	list_display = ('title', 'professional', 'listing_type', 'category', 'city', 'price_from', 'is_active', 'created_at')
	list_filter = ('is_active', 'listing_type', 'category', 'city')
	search_fields = ('title', 'description', 'city', 'address', 'professional__username')
	prepopulated_fields = {'slug': ('title',)}


@admin.register(ListingType)
class ListingTypeAdmin(admin.ModelAdmin):
	list_display = ('name', 'slug', 'created_at')
	search_fields = ('name', 'slug')
	prepopulated_fields = {'slug': ('name',)}
