import sys


sys.path.append("../front_end")

from utils.stopwords_psych import PSYCH_STOPWORDS
import bz2
import pickle as pkl
import re

import numpy as np

import pandas as pd

from utils.spacy_wrapper import get_spacy_model

INPUT_FILE = "../data/raw_questionnaires/British Cohort Studies/Final harmonised item tool EM.xlsx"
OUTPUT_FOLDER = "../front_end/models/"
OUTPUT_FILE = OUTPUT_FOLDER + "/question_category_classifier.pkl.bz2"
DIAGNOSTICS_FOLDER = "diagnostics"
DIAGNOSTICS_FILE = DIAGNOSTICS_FOLDER + "/question_category_classifier_diagnostics.txt"
DIAGNOSTICS_TRAINING_DATA_FILE = DIAGNOSTICS_FOLDER + "/question_category_classifier_data.xlsx"

NUM_FEATURES = 500

texts = []
labels = []
nlp = get_spacy_model("en")
for sheet_name in ("Adulthood", "Childhood"):
    df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)

    if sheet_name == "Adulthood":
        df = df[df.columns[4:]]
    else:
        df = df[df.columns[5:]]

    for idx in range(0, len(df)):
        for j in range(len(df.columns)):
            col_name = df.columns[j]
            text = df[col_name].iloc[idx]
            if type(text) is str and len(text) > 1:
                label = col_name

                label = re.sub(r'( – | - |/|\().*', '', label).strip().lower()
                label = re.sub(r'wothlessness', 'worthlessness', label)
                label = re.sub(r'disturbed appetite', 'appetite disturbance', label)
                label = re.sub(r'distracted', 'attention span', label)

                text = re.sub(r'" or "|\(', '/', text)

                for sub_text in text.split("/"):

                    sub_text = re.sub(r'^\s*\d+\.', '', sub_text).strip()

                    if len(sub_text) > 0:
                        doc = nlp(sub_text)

                        preprocessed_tokens = [t.lemma_.lower() for t in doc]

                        preprocessed_text = " ".join(preprocessed_tokens)

                        texts.append(preprocessed_text)
                        labels.append(label)

                        texts.append(col_name)
                        labels.append(label)

df = pd.DataFrame({"text": texts, "ground_truth": labels})
df.drop_duplicates(inplace=True, ignore_index=True)

df.to_excel(DIAGNOSTICS_TRAINING_DATA_FILE, index=False)

print(f"There are {len(df)} instances")
print("Class breakdowns:")
print(df.ground_truth.value_counts())

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline


stops = PSYCH_STOPWORDS


# Specially engineered regex to include 95%, 95%ci, etc
vectoriser = CountVectorizer(lowercase=True, max_features=500, stop_words=stops,
                             token_pattern=r'[a-zA-ZÀ-ÿ][a-zA-ZÀ-ÿ]+')
transformer = TfidfTransformer()

nb = MultinomialNB()
model = make_pipeline(vectoriser, transformer, nb)

accuracies = []
for idx in range(len(df)):
    df_train = df.drop([idx])
    df_test = df.iloc[[idx]]

    model.fit(df.text, df.ground_truth)
    y_pred = model.predict(df_test.text)

    accuracies.append(accuracy_score(df_test["ground_truth"], y_pred))

print(accuracies)
print(np.mean(accuracies))

print(f"Writing model to {OUTPUT_FILE}")

with bz2.open(OUTPUT_FILE, "wb") as f:
    pkl.dump(model, f)

print(f"\tSaved model to {OUTPUT_FILE}")

import numpy as np

fake_document = " ".join(vectoriser.vocabulary_)
vectorised_document = vectoriser.transform([fake_document])
transformed_document = transformer.transform(vectorised_document)
probas = np.zeros((transformed_document.shape[1]))

with open(DIAGNOSTICS_FILE, "w", encoding="utf-8") as f:
    for prediction_idx in range(len(model.classes_)):
        f.write(f"Strongest predictors for class {prediction_idx} {model.classes_[prediction_idx]}\n")
        for i in range(transformed_document.shape[1]):
            zeros = np.zeros(transformed_document.shape)
            zeros[0, i] = transformed_document[0, i]
            proba = nb.predict_log_proba(zeros)
            probas[i] = proba[0, prediction_idx]

        for ctr, j in enumerate(np.argsort(-probas)):
            for w, i in vectoriser.vocabulary_.items():
                if i == j:
                    f.write(f"{ctr}\t{w}\n")
