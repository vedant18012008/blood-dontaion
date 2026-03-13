from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.models import DonorProfile


class Command(BaseCommand):
    help = 'Unlock donor availability when next eligible date is reached.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        qs = DonorProfile.objects.filter(is_available=False, next_eligible_date__isnull=False, next_eligible_date__lte=today)
        count = qs.update(is_available=True)
        self.stdout.write(self.style.SUCCESS(f'Unlocked {count} donor(s).'))
