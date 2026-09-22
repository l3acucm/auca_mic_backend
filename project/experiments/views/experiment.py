import random

import structlog
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from project.experiments import serializers
from project.experiments.models import Experiment, Session

logger = structlog.get_logger(__name__)


class ExperimentPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class ExperimentViewSet(ModelViewSet):
    permission_classes = [ExperimentPermission]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    serializers_of_view_actions = {
        'list': serializers.ExperimentListSerializer,
        'retrieve': serializers.ExperimentDetailSerializer,
        'create': serializers.ExperimentCreateSerializer,
        'partial_update': serializers.ExperimentUpdateSerializer,
        'start_session': serializers.SessionCreateSerializer,
    }

    def get_serializer_class(self):
        return self.serializers_of_view_actions.get(self.action, serializers.ExperimentDetailSerializer)

    def get_queryset(self):
        return (
            Experiment.objects.filter(user=self.request.user)
            .select_related('stimulus_set')
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        experiment = serializer.save()
        return Response(
            serializers.ExperimentDetailSerializer(experiment).data, status=status.HTTP_201_CREATED
        )

    def partial_update(self, request, *args, **kwargs):
        experiment = self.get_object()
        serializer = self.get_serializer(experiment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializers.ExperimentDetailSerializer(experiment).data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        experiment = self.get_object()
        experiment.status = Experiment.Status.ARCHIVED
        experiment.save(update_fields=['status', 'updated_at'])
        return Response(serializers.ExperimentDetailSerializer(experiment).data)

    @action(detail=True, methods=['post'], url_path='start-session')
    def start_session(self, request, pk=None):
        """BRD 2.8/2.9: launch a new attempt for a participant, return its
        session URL. `participant_id` is auto-generated (p001, p002, ...) if
        left blank."""
        experiment = self.get_object()
        serializer = self.get_serializer(data={**request.data, 'experiment': str(experiment.id)})
        serializer.is_valid(raise_exception=True)
        participant_id = serializer.validated_data.get('participant_id') or _next_participant_id(experiment)
        stimulus_filenames = list(experiment.stimulus_set.vocab_data.keys())
        random.shuffle(stimulus_filenames)
        session = Session.objects.create(
            experiment=experiment, participant_id=participant_id, stimulus_order=stimulus_filenames,
        )
        logger.info("session_started", session_id=str(session.id), experiment_id=str(experiment.id))
        return Response(serializers.SessionSerializer(session).data, status=status.HTTP_201_CREATED)


def _next_participant_id(experiment) -> str:
    count = Session.objects.filter(experiment=experiment).count()
    return f'p{count + 1:03d}'
