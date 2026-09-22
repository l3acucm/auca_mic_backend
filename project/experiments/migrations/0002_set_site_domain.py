import os

from django.conf import settings
from django.db import migrations


def set_site_domain(apps, schema_editor):
    """django-moses resolves the tenant `Site` by the `domain` the frontend
    sends. Point SITE_ID's Site row at the configured DOMAIN so login can
    find it. Idempotent — safe to re-run."""
    Site = apps.get_model('sites', 'Site')
    domain = os.environ.get('DOMAIN', 'localhost')
    Site.objects.update_or_create(
        id=settings.SITE_ID,
        defaults={'domain': domain, 'name': domain},
    )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('experiments', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(set_site_domain, noop),
    ]
