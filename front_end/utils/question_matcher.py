import bz2
import pickle as pkl
import re

import numpy as np

from utils.pt_en_dict import pt_en_map
from utils.spacy_wrapper import get_spacy_model

# stops = set(stopwords.words('english')).union(set(stopwords.words('portuguese')))
# stops = {"she", "he"}
stops = {}


class QuestionMatcher:

    def __init__(self, model_file, stops={}):
        with bz2.open(model_file, "rb") as f:
            self.tfidf = pkl.load(f)
        self.stops = stops

    def parse_questions(self, nlp, text):
        doc = nlp(text)

        tokens = [t.lemma_.lower() for t in doc]

        tokens = [t for t in tokens if t not in self.stops]

        if nlp.lang == "pt":
            preprocessed_tokens = []
            for t in tokens:
                t = re.sub(r'-me$', '', t)
                preprocessed_tokens.append(pt_en_map.get(t, t))
        else:
            preprocessed_tokens = tokens

        return " ".join(preprocessed_tokens)

    def match_questions(self, dfs):

        matches = {}

        transforms = []
        for df in dfs:
            language = df.attrs['language']
            nlp = get_spacy_model(language)

            df["parsed"] = df.question.apply(lambda q: self.parse_questions(nlp, q))

            transforms.append(self.tfidf.transform(df.parsed))

        for i in range(len(transforms)):
            for j in range(i + 1, len(transforms)):
                v1 = transforms[i]
                v2 = transforms[j]

                pairwise_similarity = v1 * v2.T

                for idx in range(v1.shape[0]):
                    scores = pairwise_similarity[idx, :].todense().flatten()
                    am = np.argmax(scores)
                    max_score = scores[0, am]
                    matches[(i, idx, j, am)] = max_score

        return matches
