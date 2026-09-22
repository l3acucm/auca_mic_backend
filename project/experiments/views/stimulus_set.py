from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import BasePermission
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from project.experiments import serializers
from project.experiments.models import StimulusSet
from project.experiments.services.stimulus_set import add_stimulus


class StimulusSetPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.user_id == request.user.id


class StimulusSetViewSet(ModelViewSet):
    permission_classes = [StimulusSetPermission]
    http_method_names = ['get', 'post', 'head', 'options']
    # 'create' takes plain JSON ({name}); 'add_stimulus' takes multipart (file).
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    serializers_of_view_actions = {
        'list': serializers.StimulusSetSerializer,
        'create': serializers.StimulusSetCreateSerializer,
        'add_stimulus': serializers.AddStimulusSerializer,
    }

    def get_serializer_class(self):
        return self.serializers_of_view_actions.get(self.action, serializers.StimulusSetDetailSerializer)

    def get_queryset(self):
        return StimulusSet.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        stimulus_set = serializer.save()
        return Response(serializers.StimulusSetDetailSerializer(stimulus_set).data, status=201)

    @action(detail=True, methods=['post'], url_path='stimuli')
    def add_stimulus(self, request, pk=None):
        """Add one image + its accepted answers to this set (BRD 2.2,
        redesigned: researchers build a set up in the UI, not a ZIP)."""
        stimulus_set = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        add_stimulus(stimulus_set, serializer.validated_data['image'], serializer.validated_data['answers'])
        stimulus_set.refresh_from_db()
        return Response(serializers.StimulusSetDetailSerializer(stimulus_set).data, status=201)
