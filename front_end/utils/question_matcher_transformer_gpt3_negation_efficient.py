# stops = set(stopwords.words('english')).union(set(stopwords.words('portuguese')))
# stops = {"she", "he"}
import re

import requests

from utils.negator import negate

stops = {}
import numpy as np
from numpy import dot
from numpy.linalg import norm
import time


def normalise_question(text):
    return re.sub(r'[^a-z0-9]', '', text.lower())


import pickle as pkl

embedding_dictionary = {}


def cosine_similarity(a, b):
    return dot(a, b) / (norm(a) * norm(b))


with open(f"gpt3_embeddings_1.pkl", "rb") as f:
    embedding_dictionary = pkl.load(f)


def get_embedding(text: str, OPENAI_API_KEY: str):
    if text in embedding_dictionary:
        return embedding_dictionary[text]
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + OPENAI_API_KEY,
    }

    json_data = {
        'input': text,
        'model': 'text-embedding-ada-002',
    }

    response = requests.post('https://api.openai.com/v1/embeddings', headers=headers, json=json_data)

    embedding = np.asarray(response.json()['data'][0]['embedding'])

    embedding_dictionary[text] = embedding
    # Cache it
    with open(f"gpt3_embeddings_{len(embedding_dictionary) % 2}.pkl", "wb") as f:
        pkl.dump(embedding_dictionary, f)
    time.sleep(5)
    print(f"Number of embeddings calculated: {len(embedding_dictionary)}")

    return embedding


class QuestionMatcherTransformerGpt3NegationEfficient:
    def __init__(self, OPENAI_API_KEY: str):
        self.OPENAI_API_KEY = OPENAI_API_KEY

    def convert_texts_to_vector(self, texts: list):
        embeddings = [get_embedding(text, self.OPENAI_API_KEY) for text in texts]
        return embeddings

    def match_questions(self, dfs, is_disable_negation=False):
        # TODO: this can be rewritten to make it more efficient, taking only a single dataframe and calculating all vectors and similarities in a single operation.

        matches = {}

        transforms = []
        transforms_neg = []
        normalised_forms = []
        for df in dfs:
            language = df.attrs.get('language', 'en')

            df["vector"] = self.convert_texts_to_vector(df.question)
            negated = df.question.apply(lambda q: negate(q, language))
            df["vector_neg"] = self.convert_texts_to_vector(negated)
            df["normalised"] = df.question.apply(normalise_question)

            transforms.append(df["vector"].tolist())
            transforms_neg.append(df["vector_neg"].tolist())
            normalised_forms.append(df["normalised"].tolist())

        similarity_function = cosine_similarity

        for i in range(len(transforms)):
            for j in range(i, len(transforms)):
                pairwise_similarity = similarity_function(transforms[i], transforms[j])
                pairwise_similarity_neg1 = similarity_function(transforms_neg[i], transforms[j])
                pairwise_similarity_neg2 = similarity_function(transforms[i], transforms_neg[j])
                pairwise_similarity_neg_mean = np.mean([pairwise_similarity_neg1, pairwise_similarity_neg2], axis=0)

                if is_disable_negation:
                    similarity_with_polarity = pairwise_similarity
                else:
                    similarity_polarity = np.sign(pairwise_similarity - pairwise_similarity_neg_mean)
                    similarity_max = np.max([pairwise_similarity, pairwise_similarity_neg_mean], axis=0)
                    similarity_with_polarity = similarity_max * similarity_polarity
                for ii in range(len(transforms[i])):
                    for jj in range(len(transforms[j])):
                        if i == j and ii == jj:
                            continue
                        matches[(i, ii, j, jj)] = similarity_with_polarity[ii, jj]

        return matches
