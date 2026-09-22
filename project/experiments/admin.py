from django.contrib import admin

from project.experiments.models import Experiment, Result, Session, StimulusSet


@admin.register(StimulusSet)
class StimulusSetAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'stimulus_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name']
    readonly_fields = ['id', 's3_path', 'vocab_data', 'created_at']


@admin.register(Experiment)
class ExperimentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'user', 'language', 'num_trials', 'status', 'created_at']
    list_filter = ['status', 'language']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'participant_id', 'experiment', 'status', 'started_at', 'completed_at']
    list_filter = ['status']
    search_fields = ['participant_id']
    readonly_fields = ['id', 'created_at', 'started_at', 'completed_at', 'stimulus_order', 'trial_data']


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'participant_id', 'experiment', 'num_correct', 'num_incorrect',
        'num_skipped', 'num_errors', 'completed_at',
    ]
    list_filter = ['completed_at']
    search_fields = ['participant_id']
    readonly_fields = ['id', 'xlsx_file_path', 'trial_data', 'completed_at']
