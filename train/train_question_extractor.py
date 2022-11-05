import sys

sys.path.append("../front_end")


import os
import pickle as pkl
import re
import sys

from langdetect import detect

from utils.question_extractor import process_text, normalise, convert_to_dataframe

INPUT_FOLDER = "../data/preprocessed_tika/"
ANNOTATIONS_FOLDER = "../data/annotations/"
OUTPUT_FOLDER = "../front_end/models/"
OUTPUT_FILE = OUTPUT_FOLDER + "/question_classifier.pkl.bz2"

DIAGNOSTICS_FOLDER = "diagnostics"
DIAGNOSTICS_FILE = DIAGNOSTICS_FOLDER + "/question_classifier_diagnostics.txt"
SUMMARY_FILE = DIAGNOSTICS_FOLDER + "/summary.txt"

NUM_FEATURES = 500

file_to_annotations = {}
for root, folder, files in os.walk(ANNOTATIONS_FOLDER):
    for file_name in files:

        if not file_name.endswith("txt"):
            continue
        print(file_name)
        pdf_file = re.sub(".txt", "", file_name)

        full_file = ANNOTATIONS_FOLDER + "/" + file_name
        #         print (full_file)
        with open(full_file, 'r', encoding="utf-8") as f:
            file_to_annotations[pdf_file] = f.read()

print(f"Loaded {len(file_to_annotations)} annotations")

file_to_pages = {}
for root, folder, files in os.walk(INPUT_FOLDER):
    for file_name in files:

        if not file_name.endswith("pkl"):
            continue
        print(file_name)
        pdf_file = re.sub(".pkl", "", file_name)

        if pdf_file not in file_to_annotations:
            continue

        full_file = INPUT_FOLDER + "/" + file_name
        #         print (full_file)
        with open(full_file, 'rb') as f:
            pages = pkl.load(f)
        file_to_pages[pdf_file] = pages

print(f"Loaded {len(file_to_pages)} files")

import spacy
from spacy.tokens import Span


def annotate_ground_truths(language, doc, annots):
    ground_truth_spans = []

    nlp_small = spacy.blank(language)

    true_annots = []

    for l in annots.split("\n"):
        if not l.startswith("OPTION"):
            l = re.sub(r'(?i)^[a-z]*\d*[a-z]*\.\s*|^[a-z]\)\.*\s*', '', l)
            l = l.strip()
            if len(l) > 0:
                true_annots.append(("QUESTION", l))
        else:
            l = re.sub(r'^OPTION:\s*', '', l)
            l = l.strip()
            if len(l) > 0:
                true_annots.append(("OPTION", l))

    normalised_doc = normalise(doc.text)

    normalised_doc_tokens = [(token.i, normalise(token.text)) for token in doc]
    normalised_doc_tokens = [t for t in normalised_doc_tokens if t[1] != ""]
    for annot_type, true_annot in true_annots:

        cleaned = normalise(true_annot)
        if cleaned not in normalised_doc:
            print("not found", cleaned, pdf_file)

        tokens = nlp_small(true_annot)
        normalised_annot_tokens = [normalise(t.text) for t in tokens]
        normalised_annot_tokens = [t for t in normalised_annot_tokens if t != ""]

        is_found = False
        for i, (token_i, t) in enumerate(normalised_doc_tokens):
            if t == normalised_annot_tokens[0]:
                is_broken_sequence = False
                for j in range(1, len(normalised_annot_tokens)):
                    if i + j >= len(normalised_doc_tokens):
                        is_broken_sequence = True
                        break
                    if normalised_annot_tokens[j] != normalised_doc_tokens[i + j][1]:
                        is_broken_sequence = True
                if not is_broken_sequence:
                    if i + j < len(normalised_doc_tokens):
                        is_found = True
                        token_start = token_i
                        token_end = normalised_doc_tokens[i + j][0]

                        # TODO: how to add span
                        # mark as groudn truth
                        ground_truth_spans.append(Span(doc, token_start, token_end, label=f"GROUND_TRUTH_{annot_type}"))

        if not is_found:
            print("not found", cleaned, pdf_file)
        else:
            pass

    for ground_truth_span in ground_truth_spans:
        gt_toks = set(range(ground_truth_span.start, ground_truth_span.end))
        for ent in ground_truth_span.doc.spans["CANDIDATE_QUESTION"]:
            ent_toks = set(range(ent.start, ent.end))
            if len(ent_toks.intersection(gt_toks)) > 0:
                if ground_truth_span.label_ == "GROUND_TRUTH_OPTION":
                    new_ground_truth = 1
                else:
                    new_ground_truth = 2
                ent._.ground_truth = max(ent._.ground_truth, new_ground_truth)


file_to_docs = {}
for pdf_file, pages in file_to_pages.items():
    text = "\n".join(pages)

    language = detect(text)
    doc = process_text(text, language)

    annots = file_to_annotations[pdf_file]
    annotate_ground_truths(language, doc, annots)

    file_to_docs[pdf_file] = doc

dfs = []
for file, doc in file_to_docs.items():
    df_this_file = convert_to_dataframe(doc, True)
    df_this_file["file"] = file
    dfs.append(df_this_file)

import pandas as pd

df = pd.concat(dfs)

from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import accuracy_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import make_pipeline

# Specially engineered regex to include 95%, 95%ci, etc
vectoriser = CountVectorizer(lowercase=True, max_features=500, stop_words=[])
transformer = TfidfTransformer()

nb = MultinomialNB()
model = make_pipeline(vectoriser, transformer, nb)

import numpy as np

accuracies = []
for file in list(sorted(set(df.file))) + [None]:
    if file is None:
        df_train = df
        df_test = df
    else:
        df_train = df[df.file != file]
        df_test = df[df.file == file]
    print(f"Training on {len(df_train)} rows, testing on {file}")

    model.fit(df_train.parsed, df_train["ground_truth"])

    if file is None:
        break

    y_pred = model.predict(df_test.parsed)

    accuracies.append(accuracy_score(df_test["ground_truth"], y_pred))
print(accuracies, np.mean(accuracies))

import numpy as np

fake_document = " ".join(vectoriser.vocabulary_)
vectorised_document = vectoriser.transform([fake_document])
transformed_document = transformer.transform(vectorised_document)
probas = np.zeros((transformed_document.shape[1]))

with open(DIAGNOSTICS_FILE, "w", encoding="utf-8") as f:
    for prediction_idx in range(3):
        f.write(f"Strongest predictors for class {prediction_idx}\n")
        for i in range(transformed_document.shape[1]):
            zeros = np.zeros(transformed_document.shape)
            zeros[0, i] = transformed_document[0, i]
            proba = nb.predict_log_proba(zeros)
            probas[i] = proba[0, prediction_idx]

        for ctr, j in enumerate(np.argsort(-probas)):
            for w, i in vectoriser.vocabulary_.items():
                if i == j:
                    f.write(f"{ctr}\t{w}\n")

# test extraction
# this would be run separately
# questions = get_questions(df_this_file)


import bz2

print(f"Writing model to {OUTPUT_FILE}")

with bz2.open(OUTPUT_FILE, "wb") as f:
    pkl.dump(model, f)

print(f"\tSaved model to {OUTPUT_FILE}")
