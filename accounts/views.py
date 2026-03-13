from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from donations.models import DonationRecord

from .forms import DonorProfileForm, UserRegistrationForm
from .models import DonorBadge, DonorProfile


def register_view(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = DonorProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            user.email = user_form.cleaned_data['email']
            user.save(update_fields=['email'])

            profile = user.donor_profile
            for field, value in profile_form.cleaned_data.items():
                setattr(profile, field, value)
            profile.save()

            messages.success(request, 'Registration successful. You can now log in.')
            return redirect('accounts:login')
    else:
        user_form = UserRegistrationForm()
        profile_form = DonorProfileForm()

    return render(
        request,
        'accounts/register.html',
        {
            'user_form': user_form,
            'profile_form': profile_form,
        },
    )


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:profile')

    form = AuthenticationForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        login(request, form.get_user())
        return redirect('accounts:profile')

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile_view(request):
    profile = request.user.donor_profile
    donation_history = DonationRecord.objects.filter(donor=request.user).order_by('-donation_date')
    badges = DonorBadge.objects.filter(user=request.user)

    return render(
        request,
        'accounts/profile.html',
        {
            'profile': profile,
            'donation_history': donation_history,
            'badges': badges,
            'profile_completeness': profile.profile_completeness,
        },
    )


@login_required
def edit_profile_view(request):
    profile = request.user.donor_profile
    if request.method == 'POST':
        form = DonorProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:profile')
    else:
        form = DonorProfileForm(instance=profile)

    return render(request, 'accounts/edit_profile.html', {'form': form})


def donor_list_view(request):
    donors = DonorProfile.objects.select_related('user').all()
    blood_group = request.GET.get('blood_group', '').strip()
    city = request.GET.get('city', '').strip()
    availability = request.GET.get('availability', 'available').strip()

    if blood_group:
        donors = donors.filter(blood_group=blood_group)
    if city:
        donors = donors.filter(city__icontains=city)

    if availability == 'available':
        donors = donors.filter(is_available=True)
    elif availability == 'unavailable':
        donors = donors.filter(is_available=False)

    donors = donors.order_by('city', 'user__username')
    paginator = Paginator(donors, 9)
    page_obj = paginator.get_page(request.GET.get('page'))

    context = {
        'donors': page_obj.object_list,
        'page_obj': page_obj,
        'selected_blood_group': blood_group,
        'selected_city': city,
        'selected_availability': availability,
        'blood_groups': DonorProfile.BLOOD_GROUP_CHOICES,
    }
    return render(request, 'accounts/donor_list.html', context)
