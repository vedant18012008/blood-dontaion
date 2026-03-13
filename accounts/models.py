from django.contrib.auth.models import User
from django.db import models


BLOOD_COMPATIBILITY = {
    'O-': ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'],
    'O+': ['A+', 'B+', 'AB+', 'O+'],
    'A-': ['A+', 'A-', 'AB+', 'AB-'],
    'A+': ['A+', 'AB+'],
    'B-': ['B+', 'B-', 'AB+', 'AB-'],
    'B+': ['B+', 'AB+'],
    'AB-': ['AB+', 'AB-'],
    'AB+': ['AB+'],
}


class DonorProfile(models.Model):
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

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='donor_profile')
    phone_number = models.CharField(max_length=20, blank=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    is_available = models.BooleanField(default=True)
    last_donation_date = models.DateField(null=True, blank=True)
    next_eligible_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} ({self.blood_group or 'N/A'})"

    @property
    def compatible_recipients(self):
        return BLOOD_COMPATIBILITY.get(self.blood_group, [])

    @property
    def profile_completeness(self):
        fields = [
            self.phone_number,
            self.blood_group,
            self.date_of_birth,
            self.gender,
            self.address,
            self.city,
            self.state,
            self.profile_picture,
        ]
        completed = sum(1 for value in fields if value)
        return int((completed / len(fields)) * 100)


class DonorBadge(models.Model):
    class BadgeType(models.TextChoices):
        FIRST_DROP = 'First Drop', 'First Drop'
        FIVE_LIVES = '5 Lives Saved', '5 Lives Saved'
        LIFESAVER_HERO = 'Lifesaver Hero', 'Lifesaver Hero'

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='donor_badges')
    badge_type = models.CharField(max_length=20, choices=BadgeType.choices)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'badge_type')
        ordering = ['awarded_at']

    def __str__(self):
        return f"{self.user.username} - {self.badge_type}"
