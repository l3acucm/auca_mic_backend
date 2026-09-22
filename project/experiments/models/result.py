import uuid

from django.db import models

__all__ = ['Result']


class Result(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(
        'experiments.Session', related_name='result', on_delete=models.CASCADE
    )
    experiment = models.ForeignKey(
        'experiments.Experiment', related_name='results', on_delete=models.CASCADE
    )
    participant_id = models.CharField(max_length=50)
    total_time_sec = models.FloatField()
    num_correct = models.PositiveIntegerField(default=0)
    num_incorrect = models.PositiveIntegerField(default=0)
    num_skipped = models.PositiveIntegerField(default=0)
    num_errors = models.PositiveIntegerField(default=0)
    xlsx_file_path = models.CharField(max_length=500)
    trial_data = models.JSONField(default=list)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-completed_at']

    def __str__(self):
        return f'Result {self.participant_id} / {self.experiment_id}'
