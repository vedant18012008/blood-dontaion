from django.conf import settings
from django.db import models


class BloodInventory(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('A+', 'A+'),
        ('A-', 'A-'),
        ('B+', 'B+'),
        ('B-', 'B-'),
        ('AB+', 'AB+'),
        ('AB-', 'AB-'),
        ('O+', 'O+'),
        ('O-', 'O-'),
    ]

    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, unique=True)
    units_available = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.blood_group}: {self.units_available} units"


class BloodRequest(models.Model):
    class Urgency(models.TextChoices):
        NORMAL = 'Normal', 'Normal'
        URGENT = 'Urgent', 'Urgent'
        CRITICAL = 'Critical', 'Critical'

    class Status(models.TextChoices):
        PENDING = 'Pending', 'Pending'
        APPROVED = 'Approved', 'Approved'
        FULFILLED = 'Fulfilled', 'Fulfilled'
        REJECTED = 'Rejected', 'Rejected'
        EXPIRED = 'Expired', 'Expired'

    BLOOD_GROUP_CHOICES = BloodInventory.BLOOD_GROUP_CHOICES

    requester_name = models.CharField(max_length=120)
    requester_phone = models.CharField(max_length=20)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES)
    units_needed = models.IntegerField()
    hospital_name = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    reason = models.TextField()
    urgency = models.CharField(max_length=10, choices=Urgency.choices, default=Urgency.NORMAL)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='blood_requests',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.blood_group} - {self.requester_name} ({self.status})"


class RequestTimelineEvent(models.Model):
    request = models.ForeignKey(BloodRequest, on_delete=models.CASCADE, related_name='timeline_events')
    event = models.CharField(max_length=120)
    status_snapshot = models.CharField(max_length=10, choices=BloodRequest.Status.choices)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Request #{self.request_id} - {self.event}"


class DonationRecord(models.Model):
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='donation_records')
    related_request = models.ForeignKey('donations.BloodRequest', on_delete=models.SET_NULL, null=True, blank=True, related_name='donation_records')
    blood_group = models.CharField(max_length=3, choices=BloodInventory.BLOOD_GROUP_CHOICES)
    units_donated = models.IntegerField()
    donation_date = models.DateField()
    hospital_or_camp = models.CharField(max_length=200)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-donation_date', '-created_at']

    def __str__(self):
        return f"{self.donor.username} donated {self.units_donated} unit(s)"


class DonationCamp(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    city = models.CharField(max_length=100)
    camp_date = models.DateField()
    max_donors = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='created_camps',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['camp_date']

    def __str__(self):
        return f"{self.title} - {self.city} ({self.camp_date})"

    @property
    def registered_count(self):
        return self.registrations.count()


class CampRegistration(models.Model):
    camp = models.ForeignKey(DonationCamp, on_delete=models.CASCADE, related_name='registrations')
    donor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='camp_registrations')
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('camp', 'donor')
        ordering = ['-registered_at']

    def __str__(self):
        return f"{self.donor.username} @ {self.camp.title}"


