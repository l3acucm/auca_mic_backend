import uuid

from django.db import models

__all__ = ['Session']


class Session(models.Model):
    """One participant's attempt at an experiment, addressed by its own UUID
    (unguessable, doubles as the session URL token — BRD 2.9/3.*)."""

    class Status(models.TextChoices):
        PENDING = 'pending'
        IN_PROGRESS = 'in_progress'
        COMPLETED = 'completed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    experiment = models.ForeignKey(
        'experiments.Experiment', related_name='sessions', on_delete=models.CASCADE
    )
    participant_id = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # Randomized stimulus order for this attempt, generated once on first
    # fetch (BRD 3.2) so a page reload doesn't reshuffle mid-attempt.
    stimulus_order = models.JSONField(default=list, blank=True)
    # Trials accumulate here as the participant answers each stimulus
    # (BRD 3.6/3.7/3.8); copied into Result.trial_data on completion.
    trial_data = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.participant_id} / {self.experiment_id} ({self.status})'
