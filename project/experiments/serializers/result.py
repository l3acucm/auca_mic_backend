from rest_framework import serializers

from project.experiments.models import Result

__all__ = ['ResultListSerializer', 'ResultDetailSerializer']


class ResultListSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Result
        fields = [
            'id', 'experiment', 'participant_id', 'completed_at', 'total_time_sec',
            'num_correct', 'num_incorrect', 'num_skipped', 'num_errors', 'download_url',
        ]

    def get_download_url(self, obj):
        from django.conf import settings
        from project.storages import PrivateMediaStorage

        url = PrivateMediaStorage().url(obj.xlsx_file_path)
        if settings.STAGING or settings.PRODUCTION:
            return url  # already an absolute, signed S3 URL
        request = self.context.get('request')
        return request.build_absolute_uri(url) if request else url


class ResultDetailSerializer(ResultListSerializer):
    class Meta(ResultListSerializer.Meta):
        fields = ResultListSerializer.Meta.fields + ['trial_data']
