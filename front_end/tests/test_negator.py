import unittest

from utils.negator import negate
from utils.topic_identifier import get_keywords_for_groups


class TestNegation(unittest.TestCase):

    def test_simple_example(self):
        text = "I never feel depressed"
        self.assertEqual("I  feel depressed", negate(text, "en"))

    def test_simple_example_pt(self):
        text = "eu me sinto deprimido"
        self.assertEqual("não eu me sinto deprimido", negate(text, "pt"))