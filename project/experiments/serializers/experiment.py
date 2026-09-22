from rest_framework import serializers

from project.experiments.models import Experiment, StimulusSet
from project.experiments.serializers.stimulus_set import StimulusSetSerializer

__all__ = [
    'ExperimentListSerializer', 'ExperimentDetailSerializer',
    'ExperimentCreateSerializer', 'ExperimentUpdateSerializer',
]


class ExperimentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experiment
        fields = ['id', 'name', 'description', 'language', 'num_trials', 'status', 'created_at']


class ExperimentDetailSerializer(serializers.ModelSerializer):
    stimulus_set = StimulusSetSerializer(read_only=True)

    class Meta:
        model = Experiment
        fields = [
            'id', 'name', 'description', 'language', 'num_trials', 'status',
            'stimulus_set', 'created_at', 'updated_at',
        ]


class ExperimentCreateSerializer(serializers.ModelSerializer):
    stimulus_set = serializers.PrimaryKeyRelatedField(queryset=StimulusSet.objects.none())

    class Meta:
        model = Experiment
        fields = ['id', 'name', 'description', 'language', 'num_trials', 'stimulus_set']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get('request')
        if request is not None:
            self.fields['stimulus_set'].queryset = StimulusSet.objects.filter(user=request.user)

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ExperimentUpdateSerializer(serializers.ModelSerializer):
    """Only name/description are editable — stimuli/vocab are fixed once
    created (BRD 2.7)."""

    class Meta:
        model = Experiment
        fields = ['name', 'description']
