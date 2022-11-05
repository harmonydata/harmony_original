import os

file_name = os.path.join(os.path.dirname(__file__), '../models/options_words.csv')

OPTIONS_WORDS = set()
with open(file_name, "r", encoding="utf-8") as f:
    for l in f:
        term = l.strip()
        OPTIONS_WORDS.add(term)
