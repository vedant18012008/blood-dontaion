from django import forms

from .models import BloodRequest, DonationCamp, DonationRecord


class StyledFieldsMixin:
    def _apply_styles(self):
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.setdefault('class', 'form-select')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class BloodRequestForm(StyledFieldsMixin, forms.ModelForm):
    class Meta:
        model = BloodRequest
        fields = [
            'requester_name',
            'requester_phone',
            'blood_group',
            'units_needed',
            'hospital_name',
            'city',
            'reason',
            'urgency',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()


class DonationRecordForm(StyledFieldsMixin, forms.ModelForm):
    class Meta:
        model = DonationRecord
        fields = [
            'blood_group',
            'units_donated',
            'donation_date',
            'hospital_or_camp',
            'notes',
        ]
        widgets = {
            'donation_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()


class DonationCampForm(StyledFieldsMixin, forms.ModelForm):
    class Meta:
        model = DonationCamp
        fields = ['title', 'description', 'location', 'city', 'camp_date', 'max_donors', 'is_active']
        widgets = {
            'camp_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styles()
