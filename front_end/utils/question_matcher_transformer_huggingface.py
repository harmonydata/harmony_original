# stops = set(stopwords.words('english')).union(set(stopwords.words('portuguese')))
# stops = {"she", "he"}
stops = {}

from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('sentence-transformers/distiluse-base-multilingual-cased-v2')


def parse_questions(text):
    embedding = model.encode(text)

    return embedding


class QuestionMatcherTransformerHuggingFace:

    def match_questions(self, dfs):

        matches = {}

        transforms = []
        for df in dfs:
            # language = df.attrs['language']
            # nlp = get_spacy_model(language)

            df["parsed"] = df.question.apply(lambda q: parse_questions(q))

            transforms.append(df["parsed"])

        for i in range(len(transforms)):
            for j in range(i + 1, len(transforms)):
                for ii in range(len(transforms[i])):
                    for jj in range(len(transforms[j])):
                        pairwise_similarity = util.dot_score(transforms[i].iloc[ii], transforms[j].iloc[jj])
                        pairwise_similarity = float(pairwise_similarity[0][0].numpy())
                        # if pairwise_similarity > 0.5:
                        matches[(i, ii, j, jj)] = pairwise_similarity

        return matches
