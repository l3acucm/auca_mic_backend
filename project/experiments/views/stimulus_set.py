import structlog
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from project.experiments import serializers
from project.experiments.models import StimulusSet
from project.experiments.services.stimulus_import import import_stimulus_archive

logger = structlog.get_logger(__name__)


class StimulusSetPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class StimulusSetViewSet(ModelViewSet):
    permission_classes = [StimulusSetPermission]
    http_method_names = ['get', 'post', 'head', 'options']
    parser_classes = [MultiPartParser, FormParser]
    serializers_of_view_actions = {
        'create': serializers.StimulusSetUploadSerializer,
    }

    def get_serializer_class(self):
        return self.serializers_of_view_actions.get(self.action, serializers.StimulusSetSerializer)

    def get_queryset(self):
        return StimulusSet.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        upload = self.get_serializer(data=request.data)
        upload.is_valid(raise_exception=True)
        stimulus_set = import_stimulus_archive(
            upload.validated_data['archive'], request.user,
            name=upload.validated_data.get('name', ''),
        )
        return Response(
            serializers.StimulusSetSerializer(stimulus_set).data, status=status.HTTP_201_CREATED
        )
