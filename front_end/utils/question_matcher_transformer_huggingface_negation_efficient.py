# stops = set(stopwords.words('english')).union(set(stopwords.words('portuguese')))
# stops = {"she", "he"}
from utils.negator import negate
import re

stops = {}
import numpy as np
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')


def parse_questions(text):
    embedding = model.encode(text)

    return embedding

def convert_texts_to_vector(texts: list):
    embeddings = model.encode(list(texts))
    return [embeddings[i] for i in range(embeddings.shape[0])]

def normalise_question(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())



class QuestionMatcherTransformerHuggingFaceNegationEfficient:

    def match_questions(self, dfs):

        matches = {}

        transforms = []
        transforms_neg = []
        normalised_forms = []
        for df in dfs:
            language = df.attrs['language']

            df["parsed"] = convert_texts_to_vector(df.question)
            negated = df.question.apply(lambda q:negate(q, language))
            df["parsed_neg"] = convert_texts_to_vector(negated)
            df["normalised"] = df.question.apply(normalise_question)

            transforms.append(df["parsed"])
            transforms_neg.append(df["parsed_neg"])
            normalised_forms.append(df["normalised"])

        for i in range(len(transforms)):
            for j in range(i + 1, len(transforms)):
                pairwise_similarity = util.dot_score(transforms[i], transforms[j]).numpy()
                pairwise_similarity_neg1 = util.dot_score(transforms_neg[i], transforms[j]).numpy()
                pairwise_similarity_neg2 = util.dot_score(transforms[i], transforms_neg[j]).numpy()
                pairwise_similarity_neg_mean = np.mean([pairwise_similarity_neg1, pairwise_similarity_neg2], axis=0)

                similarity_polarity = np.sign(pairwise_similarity - pairwise_similarity_neg_mean)
                similarity_max = np.max([pairwise_similarity, pairwise_similarity_neg_mean], axis=0)
                similarity_with_polarity = similarity_max * similarity_polarity
                for ii in range(len(transforms[i])):
                    for jj in range(len(transforms[j])):
                        matches[(i, ii, j, jj)] = similarity_with_polarity[ii, jj]

        return matches
