from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Case, IntegerField, Sum, Value, When
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BloodRequestForm, DonationRecordForm
from .models import BloodInventory, BloodRequest, CampRegistration, DonationCamp, DonationRecord
from .services import build_donation_certificate_pdf


def blood_request_view(request):
    initial = {}
    if request.user.is_authenticated:
        profile = getattr(request.user, 'donor_profile', None)
        initial['requester_name'] = request.user.get_full_name() or request.user.username
        if profile and profile.phone_number:
            initial['requester_phone'] = profile.phone_number

    form = BloodRequestForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        if request.user.is_authenticated:
            duplicate_exists = BloodRequest.objects.filter(
                requested_by=request.user,
                blood_group=form.cleaned_data['blood_group'],
                status__in=[BloodRequest.Status.PENDING, BloodRequest.Status.APPROVED],
            ).exists()
            if duplicate_exists:
                messages.warning(request, 'You already have an active request for this blood group.')
                return render(request, 'donations/blood_request_form.html', {'form': form})

        blood_request = form.save(commit=False)
        if request.user.is_authenticated:
            blood_request.requested_by = request.user
        blood_request.save()
        messages.success(request, 'Blood request submitted successfully. You will receive status updates by email.')
        return redirect('donations:request_detail', request_id=blood_request.id)

    return render(request, 'donations/blood_request_form.html', {'form': form})


def request_list_view(request):
    blood_group = request.GET.get('blood_group', '').strip()
    status = request.GET.get('status', '').strip()

    requests_qs = BloodRequest.objects.all()
    if blood_group:
        requests_qs = requests_qs.filter(blood_group=blood_group)
    if status:
        requests_qs = requests_qs.filter(status=status)

    urgency_order = Case(
        When(urgency=BloodRequest.Urgency.CRITICAL, then=Value(0)),
        When(urgency=BloodRequest.Urgency.URGENT, then=Value(1)),
        default=Value(2),
        output_field=IntegerField(),
    )
    requests_qs = requests_qs.annotate(urgency_rank=urgency_order).order_by('urgency_rank', '-created_at')

    paginator = Paginator(requests_qs, 10)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page_obj,
        'requests': page_obj.object_list,
        'blood_groups': BloodInventory.BLOOD_GROUP_CHOICES,
        'statuses': BloodRequest.Status.choices,
        'selected_blood_group': blood_group,
        'selected_status': status,
    }
    return render(request, 'donations/request_list.html', context)


def request_detail_view(request, request_id):
    blood_request = get_object_or_404(BloodRequest, pk=request_id)
    donated_units = blood_request.donation_records.aggregate(total=Sum('units_donated')).get('total') or 0
    progress_percent = min(100, int((donated_units / blood_request.units_needed) * 100)) if blood_request.units_needed else 0
    can_donate = request.user.is_authenticated and request.user != blood_request.requested_by

    return render(
        request,
        'donations/request_detail.html',
        {
            'blood_request': blood_request,
            'timeline_events': blood_request.timeline_events.all(),
            'can_donate': can_donate,
            'donated_units': donated_units,
            'progress_percent': progress_percent,
        },
    )


def inventory_view(request):
    inventory = BloodInventory.objects.all().order_by('blood_group')
    return render(request, 'donations/inventory.html', {'inventory': inventory})


@login_required
def my_requests_view(request):
    my_requests = BloodRequest.objects.filter(requested_by=request.user).order_by('-created_at')
    return render(request, 'donations/my_requests.html', {'requests': my_requests})


@login_required
def donate_view(request):
    request_id = request.GET.get('request_id')
    linked_request = None
    initial = {}

    if request_id:
        linked_request = get_object_or_404(BloodRequest, pk=request_id)
        initial = {
            'blood_group': linked_request.blood_group,
            'hospital_or_camp': linked_request.hospital_name,
        }

    form = DonationRecordForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        donation = form.save(commit=False)
        donation.donor = request.user
        if linked_request:
            donation.related_request = linked_request
        donation.save()

        messages.success(request, 'Donation recorded. You are marked unavailable for 90 days and can download your certificate.')
        return redirect('accounts:profile')

    return render(request, 'donations/donate.html', {'form': form, 'linked_request': linked_request})


@login_required
def donation_certificate_view(request, donation_id):
    donation = get_object_or_404(DonationRecord, pk=donation_id)
    if request.user != donation.donor and not request.user.is_staff:
        raise Http404('Certificate not found')

    pdf_buffer = build_donation_certificate_pdf(donation)
    if not pdf_buffer:
        messages.error(request, 'PDF generator dependency is missing. Install reportlab.')
        return redirect('accounts:profile')

    response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="donation-certificate-{donation.id}.pdf"'
    return response


def camps_view(request):
    camps = DonationCamp.objects.filter(is_active=True).order_by('camp_date')
    registrations = set()
    if request.user.is_authenticated:
        registrations = set(
            CampRegistration.objects.filter(donor=request.user, camp__in=camps).values_list('camp_id', flat=True)
        )

    return render(
        request,
        'donations/camps.html',
        {
            'camps': camps,
            'registrations': registrations,
        },
    )


@login_required
def camp_register_view(request, camp_id):
    camp = get_object_or_404(DonationCamp, pk=camp_id, is_active=True)

    if camp.registrations.count() >= camp.max_donors:
        messages.error(request, 'This camp is full.')
        return redirect('donations:camps')

    CampRegistration.objects.get_or_create(camp=camp, donor=request.user)
    messages.success(request, 'You are registered for this donation camp.')
    return redirect('donations:camps')
