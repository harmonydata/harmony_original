import os
import unittest

from utils.options_extractor import add_candidate_options
from utils.question_extractor import QuestionExtractor
from utils.question_extractor import process_text, convert_to_dataframe

file_name = os.path.join(os.path.dirname(__file__),
                         "../../data/preprocessed_text/APA_DSM5_Severity-Measure-For-Depression-Child-Age-11-to-17.pdf.txt")
model_path = os.path.join(os.path.dirname(__file__), "../models/question_classifier.pkl.bz2")

with open(file_name, "r",
          encoding="utf-8") as f:
    text = f.read()

doc = process_text(text, "en")
df = convert_to_dataframe(doc)
question_extractor = QuestionExtractor(model_path)
df_questions = question_extractor.get_questions(df)
add_candidate_options(df_questions, doc)


class TestSequence(unittest.TestCase):

    def test_questions_correct_number(self):
        self.assertEqual(9, len(df_questions))

    def test_question_1_correct(self):
        self.assertEqual("Feeling down, depressed, irritable, or hopeless?", df_questions.question.iloc[0])

    def test_question_numbering_correct(self):
        self.assertEqual("8", df_questions.question_no.iloc[7])

    def test_options_correct(self):
        self.assertEqual("Not at all/Several days/More than half the days/Nearly every day",
                         df_questions.options.iloc[3])
