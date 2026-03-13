from django.db import migrations


BLOOD_GROUPS = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']


def seed_inventory(apps, schema_editor):
    BloodInventory = apps.get_model('donations', 'BloodInventory')
    for group in BLOOD_GROUPS:
        BloodInventory.objects.get_or_create(blood_group=group, defaults={'units_available': 0})


def unseed_inventory(apps, schema_editor):
    BloodInventory = apps.get_model('donations', 'BloodInventory')
    BloodInventory.objects.filter(blood_group__in=BLOOD_GROUPS, units_available=0).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('donations', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_inventory, reverse_code=unseed_inventory),
    ]
