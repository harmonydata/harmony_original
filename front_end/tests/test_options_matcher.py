import unittest

import spacy

from utils.spacy_options_matcher import create_options_matcher


class TestOptions(unittest.TestCase):

    def test_simple_options(self):
        text = """


         None of 
        the time 

        Rarely 
        Some of 
        the time 

        Often 
        All of 

        the time 

        1 
        There is always someone I can talk to about 
        my day-to-day problems """

        nlp = spacy.load("en_core_web_sm")
        doc = nlp(text)

        options_matcher = create_options_matcher(nlp)

        sequences = options_matcher(doc)

        for _, start, end in sequences:
            print(doc[start:end])
        self.assertEqual(6, len(sequences))
