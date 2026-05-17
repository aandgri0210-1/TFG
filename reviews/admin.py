from django.contrib import admin

from .models import Review, ReviewReport


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
	list_display = ('service', 'title', 'reviewer', 'rating', 'created_at')
	list_filter = ('rating', 'created_at')
	search_fields = ('service__title', 'title', 'reviewer__username', 'comment')


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
	list_display = ('review', 'reporter', 'reason', 'created_at', 'is_resolved')
	list_filter = ('reason', 'created_at', 'is_resolved')
	search_fields = ('review__title', 'reporter__username', 'description')
	readonly_fields = ('created_at', 'resolved_at')
