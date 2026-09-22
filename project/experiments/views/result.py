import django_filters
from django.http import HttpResponse
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.viewsets import ReadOnlyModelViewSet

from project.experiments import serializers
from project.experiments.models import Result
from project.experiments.services.xlsx_export import build_experiment_workbook


class ResultFilter(django_filters.FilterSet):
    experiment = django_filters.UUIDFilter(field_name='experiment_id')
    participant_id = django_filters.CharFilter(lookup_expr='icontains')
    date_from = django_filters.DateFilter(field_name='completed_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='completed_at', lookup_expr='lte')

    class Meta:
        model = Result
        fields = ['experiment', 'participant_id', 'date_from', 'date_to']


class ResultPermission(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.experiment.user_id == request.user.id


class ResultViewSet(ReadOnlyModelViewSet):
    permission_classes = [ResultPermission]
    filterset_class = ResultFilter
    serializers_of_view_actions = {
        'list': serializers.ResultListSerializer,
        'retrieve': serializers.ResultDetailSerializer,
    }

    def get_serializer_class(self):
        return self.serializers_of_view_actions.get(self.action, serializers.ResultDetailSerializer)

    def get_queryset(self):
        return Result.objects.filter(experiment__user=self.request.user).select_related('experiment')

    @action(detail=False, methods=['get'], url_path='export')
    def export_experiment(self, request):
        """All completed results of one experiment as a single XLSX (BRD 6.2).
        `?experiment=<id>` required."""
        results = self.filter_queryset(self.get_queryset())
        experiment_id = request.query_params.get('experiment')
        experiment = results.first().experiment if results.exists() else None
        wb = build_experiment_workbook(experiment, results.order_by('participant_id'))
        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename="experiment_{experiment_id}.xlsx"'
        wb.save(response)
        return response
