import bz2
import pickle as pkl
import re
import traceback
import sys


from utils.language_utils import get_clean_language_code
from utils.pt_en_dict import pt_en_map
from utils.spacy_wrapper import get_spacy_model


def parse_questions(nlp, text):
    doc = nlp(text)

    tokens = [t.lemma_.lower() for t in doc]

    if nlp.lang == "pt":
        preprocessed_tokens = []
        for t in tokens:
            t = re.sub(r'-me$', '', t)
            preprocessed_tokens.append(pt_en_map.get(t, t))
    else:
        preprocessed_tokens = tokens

    return " ".join(preprocessed_tokens)


class QuestionCategoryClassifier:

    def __init__(self, model_file):
        with bz2.open(model_file, "rb") as f:
            self.model = pkl.load(f)

    def categorise_questions(self, df):
        # language = df.attrs['language']
        # nlp = get_spacy_model(language)

        parsed_questions = df.apply(lambda r: parse_questions(get_spacy_model(get_clean_language_code(r.language)), r.question), axis=1)

        try:
            categories = self.model.predict(parsed_questions)
            # Override if empty strings
            for i in range(len(df)):
                lc = df.question.iloc[i].strip().lower()
                if lc == "":
                    categories[i] = ""

            df["question_category"] = categories
        except:
            print ("Exception categorising questions")
            traceback.print_exception(*sys.exc_info())
            df["question_category"] = "N/A"
