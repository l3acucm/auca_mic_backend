from rest_framework import serializers

from project.experiments.models import StimulusSet

__all__ = ['StimulusSetSerializer', 'StimulusSetUploadSerializer']


class StimulusSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = StimulusSet
        fields = ['id', 'name', 'stimulus_count', 'created_at']


class StimulusSetUploadSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True, max_length=255)
    archive = serializers.FileField()
