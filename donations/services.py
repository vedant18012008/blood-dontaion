import os
from datetime import date
from io import BytesIO

from django.conf import settings
from django.core.mail import send_mail

from accounts.models import DonorProfile


def send_request_notification_email(blood_request, subject_suffix, body):
    recipients = []
    if blood_request.requested_by and blood_request.requested_by.email:
        recipients.append(blood_request.requested_by.email)

    if not recipients:
        return

    subject = f"Blood Request Update: {subject_suffix}"
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=True,
    )


def notify_request_created(blood_request):
    body = (
        f"Your blood request for {blood_request.blood_group} has been submitted with status "
        f"{blood_request.status}. We will keep you updated."
    )
    send_request_notification_email(blood_request, "Submitted", body)


def notify_request_status_changed(blood_request, old_status):
    body = (
        f"Your blood request status changed from {old_status} to {blood_request.status}. "
        f"Hospital: {blood_request.hospital_name}, City: {blood_request.city}."
    )
    send_request_notification_email(blood_request, f"{blood_request.status}", body)


def rank_donors_for_request(blood_request, limit=5):
    donors = DonorProfile.objects.select_related('user').filter(blood_group=blood_request.blood_group)
    scored = []

    for donor in donors:
        score = 0

        if donor.is_available:
            score += 60
        else:
            score -= 40

        if donor.city and donor.city.lower() == blood_request.city.lower():
            score += 25

        if donor.last_donation_date:
            days_gap = (date.today() - donor.last_donation_date).days
            if days_gap >= 90:
                score += 20
            else:
                score -= 20
        else:
            score += 10

        if donor.phone_number:
            score += 5

        scored.append((score, donor))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [donor for _, donor in scored[:limit]]


def send_critical_sms_alerts(blood_request):
    if blood_request.urgency != blood_request.Urgency.CRITICAL:
        return

    donors = DonorProfile.objects.select_related('user').filter(
        is_available=True,
        blood_group=blood_request.blood_group,
        city__iexact=blood_request.city,
    )

    numbers = [donor.phone_number for donor in donors if donor.phone_number]
    if not numbers:
        return

    message = (
        f"Critical blood request: {blood_request.blood_group} in {blood_request.city}. "
        f"Hospital: {blood_request.hospital_name}. Contact: {blood_request.requester_phone}."
    )

    provider = os.getenv('SMS_PROVIDER', 'console').lower()
    if provider == 'fast2sms':
        _send_fast2sms(numbers, message)
    elif provider == 'twilio':
        _send_twilio(numbers, message)


def _send_fast2sms(numbers, message):
    api_key = os.getenv('FAST2SMS_API_KEY')
    if not api_key:
        return

    try:
        import requests

        requests.post(
            'https://www.fast2sms.com/dev/bulkV2',
            headers={'authorization': api_key},
            data={
                'route': 'q',
                'message': message,
                'language': 'english',
                'numbers': ','.join(numbers),
            },
            timeout=10,
        )
    except Exception:
        return


def _send_twilio(numbers, message):
    sid = os.getenv('TWILIO_ACCOUNT_SID')
    token = os.getenv('TWILIO_AUTH_TOKEN')
    from_number = os.getenv('TWILIO_FROM_NUMBER')

    if not sid or not token or not from_number:
        return

    try:
        import requests

        for number in numbers:
            requests.post(
                f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json',
                data={'From': from_number, 'To': number, 'Body': message},
                auth=(sid, token),
                timeout=10,
            )
    except Exception:
        return


def build_donation_certificate_pdf(donation):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
    except Exception:
        return None

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)

    pdf.setFont('Helvetica-Bold', 24)
    pdf.drawCentredString(300, 780, 'Certificate of Appreciation')

    pdf.setFont('Helvetica', 12)
    pdf.drawCentredString(300, 740, 'Blood Donation Management System')

    pdf.setFont('Helvetica-Bold', 16)
    pdf.drawCentredString(300, 680, donation.donor.get_full_name() or donation.donor.username)

    pdf.setFont('Helvetica', 12)
    pdf.drawCentredString(300, 650, 'is recognized for donating blood and helping save lives.')
    pdf.drawCentredString(300, 620, f'Blood Group: {donation.blood_group}')
    pdf.drawCentredString(300, 600, f'Units Donated: {donation.units_donated}')
    pdf.drawCentredString(300, 580, f'Donation Date: {donation.donation_date}')
    pdf.drawCentredString(300, 560, f'Location: {donation.hospital_or_camp}')

    pdf.setFont('Helvetica-Oblique', 10)
    pdf.drawCentredString(300, 520, 'Thank you for your life-saving contribution.')

    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer
