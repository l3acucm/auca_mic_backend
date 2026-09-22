import uuid

from django.conf import settings
from django.db import models

__all__ = ['Experiment']


class Experiment(models.Model):
    class Language(models.TextChoices):
        RU = 'ru'
        EN = 'en'

    class Status(models.TextChoices):
        ACTIVE = 'active'
        ARCHIVED = 'archived'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='experiments', on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=10, choices=Language.choices, default=Language.RU)
    num_trials = models.PositiveIntegerField()
    stimulus_set = models.ForeignKey(
        'experiments.StimulusSet', related_name='experiments', on_delete=models.PROTECT
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name
