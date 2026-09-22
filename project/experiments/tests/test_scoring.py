from django.test import SimpleTestCase

from project.experiments.services.scoring import CORRECT, INCORRECT, code_response


class ScoringTests(SimpleTestCase):
    def test_matches_case_insensitively(self):
        self.assertEqual(code_response('ЖУК', ['жук', 'букашка']), CORRECT)

    def test_matches_as_substring(self):
        self.assertEqual(code_response('это жук наверное', ['жук']), CORRECT)

    def test_no_match_is_incorrect(self):
        self.assertEqual(code_response('дерево', ['жук', 'букашка']), INCORRECT)

    def test_empty_text_is_incorrect(self):
        self.assertEqual(code_response('', ['жук']), INCORRECT)
