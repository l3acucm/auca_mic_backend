"""Participant-facing endpoints (BRD module 3) — no auth, addressed by the
unguessable Session UUID handed out as the session URL (BRD 1.4/2.9)."""
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.routers import SimpleRouter
from rest_framework.viewsets import GenericViewSet

from moses.common.exceptions import CustomAPIException, KwargsError

from project import errors
from project.experiments import serializers
from project.experiments.models import Result, Session
from project.experiments.services import scoring
from project.experiments.services.xlsx_export import (
    aggregate_trials, build_result_workbook, result_filename, save_result_workbook,
)


class PublicSessionViewSet(GenericViewSet):
    permission_classes = [AllowAny]
    queryset = Session.objects.select_related('experiment', 'experiment__stimulus_set')
    serializer_class = serializers.PublicSessionSerializer

    def retrieve(self, request, pk=None):
        session = self.get_object()
        if session.status == Session.Status.PENDING:
            session.status = Session.Status.IN_PROGRESS
            session.started_at = timezone.now()
            session.save(update_fields=['status', 'started_at'])
        return Response(self.get_serializer(session).data)

    @action(detail=True, methods=['post'])
    def trials(self, request, pk=None):
        session = self.get_object()
        if session.status == Session.Status.COMPLETED:
            raise CustomAPIException({'': [KwargsError(code=errors.SESSION_ALREADY_COMPLETED)]})

        serializer = serializers.TrialInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if data['stimulus_filename'] not in session.experiment.stimulus_set.vocab_data:
            raise CustomAPIException({
                'stimulus_filename': [KwargsError(code=errors.UNKNOWN_STIMULUS)]
            })

        # No transcript to check against the vocab (see TrialInputSerializer)
        # — 'recognized' just means a voice was detected at all.
        code = {
            'recognized': scoring.CORRECT,
            'skipped': scoring.SKIPPED,
            'timeout': scoring.ERROR,
            'speech_error': scoring.ERROR,
        }[data['event']]

        session.trial_data.append({
            'stimulus_filename': data['stimulus_filename'],
            'reaction_time_sec': data['reaction_time_sec'],
            'code': code,
            # Kept alongside `code` (both map to code=3) so timeout vs a real
            # recognition error are distinguishable when debugging — 'code'
            # alone can't tell them apart after the fact.
            'event': data['event'],
            'timestamp_stimulus': data['timestamp_stimulus'].isoformat(),
            'timestamp_speech_start': (
                data['timestamp_speech_start'].isoformat() if data['timestamp_speech_start'] else None
            ),
        })
        session.save(update_fields=['trial_data'])
        return Response({'code': code}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        session = self.get_object()
        if session.status == Session.Status.COMPLETED:
            raise CustomAPIException({'': [KwargsError(code=errors.SESSION_ALREADY_COMPLETED)]})

        aggregates = aggregate_trials(session.trial_data)
        completed_at = timezone.now()
        wb = build_result_workbook(
            session.participant_id, session.trial_data, aggregates, completed_at
        )
        filename = result_filename(session.participant_id, session.experiment_id)
        xlsx_path = save_result_workbook(wb, session.participant_id, filename)

        result = Result.objects.create(
            session=session, experiment=session.experiment, participant_id=session.participant_id,
            total_time_sec=aggregates['total_time_sec'], num_correct=aggregates['num_correct'],
            num_incorrect=aggregates['num_incorrect'], num_skipped=aggregates['num_skipped'],
            num_errors=aggregates['num_errors'], xlsx_file_path=xlsx_path, trial_data=session.trial_data,
        )
        session.status = Session.Status.COMPLETED
        session.completed_at = completed_at
        session.save(update_fields=['status', 'completed_at'])
        return Response({'status': 'completed', 'result_id': str(result.id)})


public_router = SimpleRouter()
public_router.register('sessions', PublicSessionViewSet, 'PublicSession')
public_urlpatterns = public_router.urls
