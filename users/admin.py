from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import Profile, User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
	model = User
	list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_staff')
	list_filter = ('role', 'is_staff', 'is_active')
	fieldsets = BaseUserAdmin.fieldsets + (('Marketplace', {'fields': ('role',)}),)
	add_fieldsets = BaseUserAdmin.add_fieldsets + (('Marketplace', {'fields': ('role',)}),)
	search_fields = ('username', 'first_name', 'last_name', 'email')


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
	list_display = ('user', 'city', 'phone', 'updated_at')
	search_fields = ('user__username', 'user__email', 'city', 'phone')
