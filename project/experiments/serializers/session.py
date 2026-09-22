from django.conf import settings
from rest_framework import serializers

from project.experiments.models import Experiment, Session

__all__ = ['SessionCreateSerializer', 'SessionSerializer']


class SessionCreateSerializer(serializers.ModelSerializer):
    experiment = serializers.PrimaryKeyRelatedField(queryset=Experiment.objects.none())

    class Meta:
        model = Session
        fields = ['id', 'experiment', 'participant_id']
        extra_kwargs = {'participant_id': {'required': False, 'allow_blank': True}}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request is not None:
            self.fields['experiment'].queryset = Experiment.objects.filter(user=request.user)


class SessionSerializer(serializers.ModelSerializer):
    session_url = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = ['id', 'experiment', 'participant_id', 'status', 'session_url', 'created_at']

    def get_session_url(self, obj):
        base = settings.FRONTEND_ORIGINS[0] if settings.FRONTEND_ORIGINS else settings.URL_PREFIX
        return f'{base.rstrip("/")}/s/{obj.id}'
