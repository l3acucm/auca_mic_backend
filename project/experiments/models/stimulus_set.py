import uuid

from django.conf import settings
from django.db import models

__all__ = ['StimulusSet']


class StimulusSet(models.Model):
    """A collection of stimuli (image + accepted answers), built up one image
    at a time in the researcher UI. Reusable by any number of experiments
    (BRD 2.5/2.6, "Experiment -> StimulusSet many:1")."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='stimulus_sets', on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, blank=True)
    # {"beetle.jpg": ["жук", "букашка"], "leaf.jpg": ["лист", "листик"]}
    vocab_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def s3_path(self) -> str:
        return f'stimulus_sets/{self.id}/'

    @property
    def stimulus_count(self) -> int:
        return len(self.vocab_data)

    def __str__(self):
        return self.name or f'StimulusSet {self.id}'
