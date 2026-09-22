from rest_framework import serializers

from project.experiments.models import StimulusSet

__all__ = [
    'StimulusSetSerializer', 'StimulusSetDetailSerializer',
    'StimulusSetCreateSerializer', 'AddStimulusSerializer',
]


class StimulusSetSerializer(serializers.ModelSerializer):
    stimulus_count = serializers.ReadOnlyField()

    class Meta:
        model = StimulusSet
        fields = ['id', 'name', 'stimulus_count', 'created_at']


class StimulusSetDetailSerializer(StimulusSetSerializer):
    stimuli = serializers.SerializerMethodField()

    class Meta(StimulusSetSerializer.Meta):
        fields = StimulusSetSerializer.Meta.fields + ['stimuli']

    def get_stimuli(self, obj):
        from project.storages import PublicMediaStorage
        storage = PublicMediaStorage()
        return [
            {'filename': filename, 'answers': answers, 'url': storage.url(f'{obj.s3_path}{filename}')}
            for filename, answers in obj.vocab_data.items()
        ]


class StimulusSetCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StimulusSet
        fields = ['id', 'name']

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AddStimulusSerializer(serializers.Serializer):
    image = serializers.FileField()
    answers = serializers.CharField()
