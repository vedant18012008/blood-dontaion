from django.db.models import Case, IntegerField, Value, When
from django.shortcuts import render

from accounts.models import DonorProfile
from donations.models import BloodInventory, BloodRequest


def home_view(request):
    total_donors = DonorProfile.objects.filter(is_available=True).count()
    fulfilled_requests = BloodRequest.objects.filter(status=BloodRequest.Status.FULFILLED).count()
    blood_groups_available = BloodInventory.objects.filter(units_available__gt=0).count()
    inventory_snapshot = BloodInventory.objects.order_by('-units_available', 'blood_group')[:4]
    urgency_order = Case(
        When(urgency=BloodRequest.Urgency.CRITICAL, then=Value(0)),
        When(urgency=BloodRequest.Urgency.URGENT, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
    urgent_requests = (
        BloodRequest.objects.filter(status__in=[BloodRequest.Status.PENDING, BloodRequest.Status.APPROVED])
        .annotate(urgency_rank=urgency_order)
        .order_by('urgency_rank', '-created_at')[:3]
    )

    context = {
        'total_donors': total_donors,
        'fulfilled_requests': fulfilled_requests,
        'blood_groups_available': blood_groups_available,
        'inventory_snapshot': inventory_snapshot,
        'urgent_requests': urgent_requests,
    }
    return render(request, 'home.html', context)
