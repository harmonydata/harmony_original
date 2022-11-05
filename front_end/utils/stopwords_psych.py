from utils.spacy_wrapper import get_spacy_model

PSYCH_STOPWORDS = set()

PSYCH_STOPWORDS = PSYCH_STOPWORDS.union(get_spacy_model("en").Defaults.stop_words)
PSYCH_STOPWORDS = PSYCH_STOPWORDS.union(get_spacy_model("pt").Defaults.stop_words)

PSYCH_STOPWORDS = PSYCH_STOPWORDS.union(
    ['able',
     'coisa',
     'different',
     'difficult',
     'dificuldade',
     'difícil',
     'easily',
     'easy',
     'feel',
     'feeling',
     'felt',
     'fácil',
     'fácilmente',
     'rate',
     'senti',
     'sentir',
     'sinto',
     'thing',
     'trouble']
)
