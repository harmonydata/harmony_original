import re

import numpy as np
from nltk.corpus import stopwords

from utils.pt_en_dict import pt_en_map
from utils.spacy_wrapper import get_spacy_model

# stops = set(stopwords.words('english')).union(set(stopwords.words('portuguese')))
# stops = {"she", "he"}
stops = {}

from sklearn.feature_extraction.text import TfidfVectorizer

STOPS = set(stopwords.words('english')).union(set(stopwords.words('portuguese')))


class QuestionMatcherNonpretrained:

    def __init__(self, stops=STOPS, is_only_include_highest_confidence=False):
        self.stops = stops
        self.is_only_include_highest_confidence = is_only_include_highest_confidence

    def parse_questions(self, nlp, text):
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

    def match_questions(self, dfs):

        matches = {}

        all_documents = []
        for df in dfs:
            language = df.attrs['language']
            nlp = get_spacy_model(language)

            df["parsed"] = df.question.apply(lambda q: self.parse_questions(nlp, q))

            all_documents.extend(df["parsed"])

        tfidf = TfidfVectorizer(lowercase=True, max_features=500, stop_words=self.stops,
                                token_pattern=r'[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ]+').fit(all_documents)

        transforms = []
        for df in dfs:
            transforms.append(tfidf.transform(df.parsed))

        for i in range(len(transforms)):
            for j in range(i + 1, len(transforms)):
                v1 = transforms[i]
                v2 = transforms[j]

                pairwise_similarity = v1 * v2.T

                for idx in range(v1.shape[0]):
                    scores = pairwise_similarity[idx, :].todense().flatten()

                    if self.is_only_include_highest_confidence:
                        am = np.argmax(scores)
                        max_score = scores[0, am]
                        if max_score > 0:
                            matches[(i, idx, j, am)] = max_score
                    else:
                        for am in range(scores.shape[1]):
                            # am = np.argmax(scores)
                            max_score = scores[0, am]
                            matches[(i, idx, j, am)] = max_score

        return matches
