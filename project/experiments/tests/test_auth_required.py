from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class ExperimentsAuthRequiredTests(APITestCase):
    """Smoke test / CI image self-check: the researcher API is auth-gated and
    the URLconf + DRF stack wires up correctly. No external services needed."""

    def test_experiments_list_requires_auth(self):
        resp = self.client.get(reverse('experiments:Experiment-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_results_list_requires_auth(self):
        resp = self.client.get(reverse('experiments:Result-list'))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
