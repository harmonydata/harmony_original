# stops = set(stopwords.words('english')).union(set(stopwords.words('portuguese')))
# stops = {"she", "he"}
import re

from utils.negator import negate

stops = {}
import numpy as np
from sentence_transformers import SentenceTransformer, util


def normalise_question(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


class QuestionMatcherTransformerHuggingFaceNegationEfficient:

    def __init__(self, sentence_transformer_path):
        self.model = SentenceTransformer(sentence_transformer_path)

    def parse_questions(self, text):
        embedding = self.model.encode(text)

        return embedding

    def convert_texts_to_vector(self, texts: list):
        embeddings = self.model.encode(list(texts))
        return [embeddings[i] for i in range(embeddings.shape[0])]

    def match_questions(self, dfs, is_use_cosine_similarity=False, is_disable_negation=False):

        matches = {}

        transforms = []
        transforms_neg = []
        normalised_forms = []
        for df in dfs:
            language = df.attrs['language']

            df["parsed"] = self.convert_texts_to_vector(df.question)
            negated = df.question.apply(lambda q: negate(q, language))
            df["parsed_neg"] = self.convert_texts_to_vector(negated)
            df["normalised"] = df.question.apply(normalise_question)

            transforms.append(df["parsed"].tolist())
            transforms_neg.append(df["parsed_neg"].tolist())
            normalised_forms.append(df["normalised"].tolist())

        if is_use_cosine_similarity:
            similarity_function = util.cos_sim
        else:
            similarity_function = util.dot_score

        for i in range(len(transforms)):
            for j in range(i + 1, len(transforms)):
                pairwise_similarity = similarity_function(transforms[i], transforms[j]).numpy()
                pairwise_similarity_neg1 = similarity_function(transforms_neg[i], transforms[j]).numpy()
                pairwise_similarity_neg2 = similarity_function(transforms[i], transforms_neg[j]).numpy()
                pairwise_similarity_neg_mean = np.mean([pairwise_similarity_neg1, pairwise_similarity_neg2], axis=0)

                if is_disable_negation:
                    similarity_with_polarity = pairwise_similarity
                else:
                    similarity_polarity = np.sign(pairwise_similarity - pairwise_similarity_neg_mean)
                    similarity_max = np.max([pairwise_similarity, pairwise_similarity_neg_mean], axis=0)
                    similarity_with_polarity = similarity_max * similarity_polarity
                for ii in range(len(transforms[i])):
                    for jj in range(len(transforms[j])):
                        matches[(i, ii, j, jj)] = similarity_with_polarity[ii, jj]

        return matches
