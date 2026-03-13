import json

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import DonorProfile
from donations.forms import DonationCampForm
from donations.models import BloodInventory, BloodRequest, DonationCamp, DonationRecord
from donations.services import rank_donors_for_request


@staff_member_required
def dashboard_home(request):
    total_donors = DonorProfile.objects.count()
    total_requests = BloodRequest.objects.count()
    pending_requests = BloodRequest.objects.filter(status=BloodRequest.Status.PENDING).count()
    total_donations = DonationRecord.objects.count()

    context = {
        'total_donors': total_donors,
        'total_requests': total_requests,
        'pending_requests': pending_requests,
        'total_donations': total_donations,
        'inventory': BloodInventory.objects.all().order_by('blood_group'),
        'recent_pending_requests': BloodRequest.objects.filter(status=BloodRequest.Status.PENDING).order_by('-created_at')[:10],
    }
    return render(request, 'dashboard/home.html', context)


@staff_member_required
def manage_requests_view(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        new_status = request.POST.get('status')
        blood_request = get_object_or_404(BloodRequest, pk=request_id)

        if new_status in dict(BloodRequest.Status.choices):
            blood_request.status = new_status
            blood_request.save(update_fields=['status', 'updated_at'])
            messages.success(request, f'Request marked as {blood_request.status}.')

        return redirect('dashboard:manage_requests')

    requests_qs = BloodRequest.objects.all().order_by('-created_at')
    request_rows = [{'request': req, 'recommendations': rank_donors_for_request(req, limit=5)} for req in requests_qs]
    return render(request, 'dashboard/manage_requests.html', {'request_rows': request_rows, 'status_choices': BloodRequest.Status.choices})


@staff_member_required
def manage_inventory_view(request):
    inventory = BloodInventory.objects.all().order_by('blood_group')

    if request.method == 'POST':
        for item in inventory:
            field_name = f'units_{item.id}'
            if field_name in request.POST:
                try:
                    units = int(request.POST.get(field_name, item.units_available))
                    if units >= 0:
                        item.units_available = units
                        item.save(update_fields=['units_available'])
                except ValueError:
                    continue
        messages.success(request, 'Inventory updated successfully.')
        return redirect('dashboard:manage_inventory')

    return render(request, 'dashboard/manage_inventory.html', {'inventory': inventory})


@staff_member_required
def donor_list_admin_view(request):
    donors = DonorProfile.objects.select_related('user').all().order_by('user__username')
    return render(request, 'dashboard/donor_list.html', {'donors': donors})


@staff_member_required
def donation_records_view(request):
    donation_records = DonationRecord.objects.select_related('donor').all().order_by('-donation_date')
    return render(request, 'dashboard/donation_records.html', {'donation_records': donation_records})


@staff_member_required
def manage_camps_view(request):
    form = DonationCampForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        camp = form.save(commit=False)
        camp.created_by = request.user
        camp.save()
        messages.success(request, 'Donation camp created.')
        return redirect('dashboard:manage_camps')

    camps = DonationCamp.objects.all().order_by('-camp_date')
    return render(request, 'dashboard/manage_camps.html', {'form': form, 'camps': camps})


@staff_member_required
def analytics_view(request):
    monthly = (
        DonationRecord.objects.annotate(month=TruncMonth('donation_date'))
        .values('month')
        .annotate(total=Count('id'))
        .order_by('month')
    )

    most_requested = (
        BloodRequest.objects.values('blood_group').annotate(total=Count('id')).order_by('-total')
    )

    top_cities = BloodRequest.objects.values('city').annotate(total=Count('id')).order_by('-total')[:10]

    total_requests = BloodRequest.objects.count()
    fulfilled = BloodRequest.objects.filter(status=BloodRequest.Status.FULFILLED).count()
    fulfillment_rate = round((fulfilled / total_requests) * 100, 2) if total_requests else 0

    heatmap = (
        BloodRequest.objects.filter(status__in=[BloodRequest.Status.PENDING, BloodRequest.Status.APPROVED])
        .values('city', 'blood_group')
        .annotate(units_needed=Sum('units_needed'), requests=Count('id'))
        .order_by('city', 'blood_group')
    )

    context = {
        'monthly_labels': json.dumps([row['month'].strftime('%b %Y') for row in monthly]),
        'monthly_data': json.dumps([row['total'] for row in monthly]),
        'group_labels': json.dumps([row['blood_group'] for row in most_requested]),
        'group_data': json.dumps([row['total'] for row in most_requested]),
        'top_cities': top_cities,
        'fulfillment_rate': fulfillment_rate,
        'heatmap': heatmap,
    }
    return render(request, 'dashboard/analytics.html', context)

