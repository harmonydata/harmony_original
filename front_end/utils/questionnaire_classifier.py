import bz2
import pickle as pkl
import re

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


class QuestionnaireClassifier:

    def __init__(self, model_file):
        with bz2.open(model_file, "rb") as f:
            self.model = pkl.load(f)

    def categorise_questionnaire(self, text, language):
        nlp = get_spacy_model(language)

        parsed_questionnaire = parse_questions(nlp, text)

        return self.model.predict([parsed_questionnaire])[0]
