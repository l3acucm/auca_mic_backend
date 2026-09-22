from rest_framework.routers import SimpleRouter

from project.experiments import views

app_name = 'experiments'

router = SimpleRouter()
router.register('stimulus-sets', views.StimulusSetViewSet, 'StimulusSet')
router.register('experiments', views.ExperimentViewSet, 'Experiment')
router.register('results', views.ResultViewSet, 'Result')

urlpatterns = router.urls
