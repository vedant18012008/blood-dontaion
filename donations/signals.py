from datetime import timedelta

from django.db.models import F, Sum
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from accounts.services import award_donor_badges

from .models import BloodInventory, BloodRequest, DonationRecord, RequestTimelineEvent
from .services import notify_request_created, notify_request_status_changed, send_critical_sms_alerts


@receiver(pre_save, sender=BloodRequest)
def capture_old_request_status(sender, instance, **kwargs):
    if not instance.pk:
        instance._old_status = None
        return

    try:
        old = BloodRequest.objects.get(pk=instance.pk)
        instance._old_status = old.status
    except BloodRequest.DoesNotExist:
        instance._old_status = None


@receiver(post_save, sender=BloodRequest)
def create_timeline_and_notify(sender, instance, created, **kwargs):
    if created:
        RequestTimelineEvent.objects.create(
            request=instance,
            event='Request Submitted',
            status_snapshot=instance.status,
            note='Blood request submitted successfully.',
        )
        notify_request_created(instance)
        send_critical_sms_alerts(instance)
        return

    old_status = getattr(instance, '_old_status', None)
    if old_status and old_status != instance.status:
        RequestTimelineEvent.objects.create(
            request=instance,
            event='Status Updated',
            status_snapshot=instance.status,
            note=f'Status changed from {old_status} to {instance.status}.',
        )
        notify_request_status_changed(instance, old_status)


@receiver(post_save, sender=DonationRecord)
def update_inventory_on_donation(sender, instance, created, **kwargs):
    if not created:
        return

    inventory, _ = BloodInventory.objects.get_or_create(
        blood_group=instance.blood_group,
        defaults={'units_available': 0},
    )
    BloodInventory.objects.filter(pk=inventory.pk).update(units_available=F('units_available') + instance.units_donated)
    award_donor_badges(instance.donor)

    profile = instance.donor.donor_profile
    profile.last_donation_date = instance.donation_date
    profile.next_eligible_date = instance.donation_date + timedelta(days=90)
    profile.is_available = False
    profile.save(update_fields=['last_donation_date', 'next_eligible_date', 'is_available'])

    if instance.related_request_id:
        req = instance.related_request
        total = DonationRecord.objects.filter(related_request=req).aggregate(total=Sum('units_donated')).get('total') or 0
        old_status = req.status
        if total >= req.units_needed:
            req.status = BloodRequest.Status.FULFILLED
        elif req.status == BloodRequest.Status.PENDING:
            req.status = BloodRequest.Status.APPROVED

        if req.status != old_status:
            req.save(update_fields=['status', 'updated_at'])
            RequestTimelineEvent.objects.create(
                request=req,
                event='Donation Matched',
                status_snapshot=req.status,
                note=f'{instance.donor.username} donated {instance.units_donated} unit(s).',
            )
