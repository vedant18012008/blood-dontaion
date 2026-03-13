from django.core.management.base import BaseCommand
from django.utils import timezone

from donations.models import BloodRequest, RequestTimelineEvent


class Command(BaseCommand):
    help = 'Expire pending requests older than 7 days.'

    def handle(self, *args, **options):
        cutoff = timezone.now() - timezone.timedelta(days=7)
        expired = BloodRequest.objects.filter(
            status=BloodRequest.Status.PENDING,
            created_at__lt=cutoff,
        )

        count = 0
        for req in expired:
            req.status = BloodRequest.Status.EXPIRED
            req.save(update_fields=['status', 'updated_at'])
            RequestTimelineEvent.objects.create(
                request=req,
                event='Request Auto-Expired',
                status_snapshot=req.status,
                note='Pending request automatically expired after 7 days.',
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Expired {count} request(s).'))

