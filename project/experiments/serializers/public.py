from rest_framework import serializers

from project.experiments.models import Session

__all__ = ['PublicSessionSerializer', 'TrialInputSerializer']


class PublicSessionSerializer(serializers.ModelSerializer):
    """Participant-facing session state — no vocab, no researcher/user data
    (BRD module 3: the participant only ever sees images + instructions)."""
    language = serializers.CharField(source='experiment.language', read_only=True)
    num_trials = serializers.IntegerField(source='experiment.num_trials', read_only=True)
    stimuli = serializers.SerializerMethodField()

    class Meta:
        model = Session
        fields = ['id', 'status', 'language', 'num_trials', 'stimuli']

    def get_stimuli(self, obj):
        from django.conf import settings
        from project.storages import PublicMediaStorage

        storage = PublicMediaStorage()
        stimulus_set = obj.experiment.stimulus_set
        request = self.context.get('request')

        def resolve(filename):
            url = storage.url(f'{stimulus_set.s3_path}{filename}')
            if (settings.STAGING or settings.PRODUCTION) or request is None:
                return url
            return request.build_absolute_uri(url)

        return [{'filename': f, 'url': resolve(f)} for f in obj.stimulus_order]


class TrialInputSerializer(serializers.Serializer):
    stimulus_filename = serializers.CharField()
    reaction_time_sec = serializers.FloatField(min_value=0)
    recognized_text = serializers.CharField(required=False, allow_blank=True, default='')
    event = serializers.ChoiceField(choices=['recognized', 'skipped', 'timeout', 'speech_error'])
    timestamp_stimulus = serializers.DateTimeField()
    timestamp_speech_start = serializers.DateTimeField(required=False, allow_null=True, default=None)
