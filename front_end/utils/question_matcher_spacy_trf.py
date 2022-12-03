from utils.spacy_wrapper import get_spacy_model

# stops = set(stopwords.words('english')).union(set(stopwords.words('portuguese')))
# stops = {"she", "he"}
stops = {}


def parse_questions(nlp, text):
    doc = nlp(text)

    return doc


class QuestionMatcherSpacy:

    def match_questions(self, dfs):

        matches = {}

        transforms = []
        for df in dfs:
            language = df.attrs['language']
            nlp = get_spacy_model(language)

            df["parsed"] = df.question.apply(lambda q: parse_questions(nlp, q))

            transforms.append(df["parsed"])

        for i in range(len(transforms)):
            for j in range(i + 1, len(transforms)):
                for ii in range(len(transforms[i])):
                    for jj in range(len(transforms[j])):
                        pairwise_similarity = transforms[i].iloc[ii].similarity(transforms[j].iloc[jj])

                        # if pairwise_similarity > 0.5:
                        matches[(i, ii, j, jj)] = pairwise_similarity

        return matches
