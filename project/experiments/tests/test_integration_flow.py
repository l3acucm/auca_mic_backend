"""End-to-end smoke test of the whole researcher+participant flow: upload a
stimulus ZIP, create an experiment, start a session, answer every trial, and
complete it — verifying scoring and XLSX generation actually run together,
not just each in isolation."""
import io
import zipfile

from django.contrib.sites.models import Site
from django.urls import reverse
from rest_framework.test import APITestCase

from moses.models import CustomUser
from project.experiments.models import Result, StimulusSet


def _build_zip():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w') as zf:
        zf.writestr('images/beetle.jpg', b'not-a-real-jpeg-but-fine-for-import')
        zf.writestr('images/leaf.jpg', b'not-a-real-jpeg-but-fine-for-import')
        zf.writestr('vocab.txt', 'beetle\tжук;букашка\nleaf\tлист, листик\n')
    buf.seek(0)
    return buf


class FullExperimentFlowTests(APITestCase):
    def setUp(self):
        site, _ = Site.objects.update_or_create(
            id=1, defaults={'domain': 'localhost:8000', 'name': 'localhost:8000'}
        )
        self.user = CustomUser.objects.create_user(
            phone_number='+996700000000', password='pw', site=site
        )
        self.client.force_authenticate(self.user)

    def test_full_flow(self):
        upload = self.client.post(
            reverse('experiments:StimulusSet-list'),
            {'name': 'demo set', 'archive': _build_zip()},
            format='multipart',
        )
        self.assertEqual(upload.status_code, 201, upload.data)
        stimulus_set = StimulusSet.objects.get()
        self.assertEqual(stimulus_set.stimulus_count, 2)
        self.assertEqual(set(stimulus_set.vocab_data.keys()), {'beetle.jpg', 'leaf.jpg'})

        created = self.client.post(reverse('experiments:Experiment-list'), {
            'name': 'Naming task', 'description': '', 'language': 'ru',
            'num_trials': 2, 'stimulus_set': str(stimulus_set.id),
        })
        self.assertEqual(created.status_code, 201, created.data)
        experiment_id = created.data['id']

        started = self.client.post(
            reverse('experiments:Experiment-start-session', args=[experiment_id]), {}
        )
        self.assertEqual(started.status_code, 201, started.data)
        session_id = started.data['id']
        self.assertIn(f'/s/{session_id}', started.data['session_url'])

        self.client.force_authenticate(None)  # participant flow is unauthenticated
        state = self.client.get(reverse('PublicSession-detail', args=[session_id]))
        self.assertEqual(state.status_code, 200, state.data)
        stimuli = state.data['stimuli']
        self.assertEqual(len(stimuli), 2)

        for stim in stimuli:
            correct_word = stimulus_set.vocab_data[stim['filename']][0]
            trial = self.client.post(
                reverse('PublicSession-trials', args=[session_id]), {
                    'stimulus_filename': stim['filename'],
                    'reaction_time_sec': 0.5,
                    'recognized_text': correct_word,
                    'event': 'recognized',
                    'timestamp_stimulus': '2026-09-22T10:00:00Z',
                    'timestamp_speech_start': '2026-09-22T10:00:00.5Z',
                },
            )
            self.assertEqual(trial.status_code, 201, trial.data)
            self.assertEqual(trial.data['code'], 1)

        complete = self.client.post(reverse('PublicSession-complete', args=[session_id]))
        self.assertEqual(complete.status_code, 200, complete.data)

        result = Result.objects.get()
        self.assertEqual(result.num_correct, 2)
        self.assertEqual(result.num_incorrect, 0)
        self.assertTrue(result.xlsx_file_path)

        self.client.force_authenticate(self.user)
        listed = self.client.get(reverse('experiments:Result-list'))
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(len(listed.data['results']), 1)
        self.assertTrue(listed.data['results'][0]['download_url'])

        exported = self.client.get(
            reverse('experiments:Result-export-experiment'), {'experiment': experiment_id}
        )
        self.assertEqual(exported.status_code, 200)
        self.assertEqual(
            exported['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
