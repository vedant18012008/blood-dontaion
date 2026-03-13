from django.contrib import admin

from .models import BloodInventory, BloodRequest, CampRegistration, DonationCamp, DonationRecord, RequestTimelineEvent


@admin.register(BloodRequest)
class BloodRequestAdmin(admin.ModelAdmin):
    list_display = ['requester_name', 'blood_group', 'units_needed', 'city', 'urgency', 'status', 'created_at']
    list_filter = ['blood_group', 'urgency', 'status', 'city']
    search_fields = ['requester_name', 'hospital_name', 'city']


@admin.register(BloodInventory)
class BloodInventoryAdmin(admin.ModelAdmin):
    list_display = ['blood_group', 'units_available', 'last_updated']
    list_filter = ['blood_group']


@admin.register(DonationRecord)
class DonationRecordAdmin(admin.ModelAdmin):
    list_display = ['donor', 'blood_group', 'units_donated', 'donation_date', 'hospital_or_camp']
    list_filter = ['blood_group', 'donation_date']
    search_fields = ['donor__username', 'hospital_or_camp']


@admin.register(DonationCamp)
class DonationCampAdmin(admin.ModelAdmin):
    list_display = ['title', 'city', 'camp_date', 'max_donors', 'is_active']
    list_filter = ['city', 'camp_date', 'is_active']
    search_fields = ['title', 'city', 'location']


@admin.register(CampRegistration)
class CampRegistrationAdmin(admin.ModelAdmin):
    list_display = ['camp', 'donor', 'registered_at']
    list_filter = ['registered_at', 'camp__city']
    search_fields = ['donor__username', 'camp__title']


@admin.register(RequestTimelineEvent)
class RequestTimelineEventAdmin(admin.ModelAdmin):
    list_display = ['request', 'event', 'status_snapshot', 'created_at']
    list_filter = ['status_snapshot', 'created_at']
    search_fields = ['request__requester_name', 'event']
