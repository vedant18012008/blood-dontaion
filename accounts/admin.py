from django.contrib import admin

from .models import DonorBadge, DonorProfile


@admin.register(DonorProfile)
class DonorProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'blood_group', 'city', 'is_available']
    list_filter = ['blood_group', 'city', 'is_available']
    search_fields = ['user__username', 'city', 'state']


@admin.register(DonorBadge)
class DonorBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge_type', 'awarded_at']
    list_filter = ['badge_type']
    search_fields = ['user__username']
