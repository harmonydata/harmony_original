import bz2
import pickle as pkl
import re

import numpy as np
import pandas as pd
from spacy.tokens import Span

from utils.pt_en_dict import pt_en_map
from utils.sequence_finder import find_longest_uninterrupted_sequence
from utils.spacy_wrapper import get_spacy_model, re_contains_num


def normalise(text):
    return re.sub(r'\W', '', text.lower())


#
# def clean(text):
#     text = re.sub(r'\s+', ' ', text).strip()
#     text = re.sub(r"^\)|\($", "", text).strip()
#     return text


def process_text(text: str, language_code: str):
    nlp = get_spacy_model(language_code)

    doc = nlp(text)

    return doc


def get_parse_features(span):
    items = []
    if "?" in span.text:
        items.append("questionmark")
    # items.append(str(span.root.pos_))
    for token in span:
        if re_contains_num.match(token.text) is not None:
            lemma = None
        elif token.is_alpha:
            lemma = token.lemma_
        else:
            lemma = None
        if lemma is not None:
            lemma = lemma.lower()
        if span.doc.lang_ == "pt" and lemma is not None:
            lemma = re.sub(r'-me$', '', lemma)
            lemma = pt_en_map.get(lemma, lemma)
        if lemma:
            items.append(lemma)
    return " ".join(items)


def clean_question(text):
    return re.sub(r'^\s*(-|\))\s*|\s*(-|\()\s*$', '', re.sub(r'\s+', ' ', text)).strip()


def get_question_from_span(question_span):
    """
    Get the text of a question, excluding any of the leading or trailing Likert options
    :param question_span:
    :return:
    """
    doc = question_span.doc
    tokens_to_include = set(range(question_span.start, question_span.end))

    # Logic to delete Likert options from end of text
    tokens_to_exclude = set()
    for option_span in doc.spans['CANDIDATE_OPTION']:
        for i in range(option_span.start, option_span.end):
            tokens_to_exclude.add(i)

    for i in tokens_to_exclude:
        if i + 1 in tokens_to_exclude or i - 1 in tokens_to_exclude:
            if i in tokens_to_include:
                tokens_to_include.remove(i)

    if len(tokens_to_include) == 0:
        return ""
    start = question_span.start
    end = max(tokens_to_include) + 1
    if start < end:
        question_span = doc[start:end]

    return clean_question(question_span.text)


def convert_to_dataframe(doc, is_training=False):
    df = pd.DataFrame({"span": list(doc.spans['CANDIDATE_QUESTION'])})

    if is_training:
        df["ground_truth"] = df.question.apply(lambda span: span._.ground_truth)

    # df["question"] = df["span"].apply(lambda span: clean_question(span.text))
    df["question"] = df["span"].apply(lambda span: get_question_from_span(span))

    df["preceding_bullet_value"] = df["span"].apply(lambda span: span._.preceding_bullet_value)

    df["parsed"] = df["span"].apply(get_parse_features)

    return df


def is_acceptable_span(span: Span) -> bool:
    if span.end - span.start < 2:
        return False
    question = get_question_from_span(span)
    non_whitespace_text = re.sub(r'\W', '',question)
    if len(non_whitespace_text) < 10:
        return False
    return True


#
#
# def clean_options(text):
#     return re.sub(r'\s+', ' ', re.sub(r'^\W+|\W+$', '', text)).upper()


class QuestionExtractor:

    def __init__(self, model_file):
        with bz2.open(model_file, "rb") as f:
            self.model = pkl.load(f)

    def get_questions(self, df):
        # TODO: put machine learning inference here

        preceding_bullet_values = list(df.preceding_bullet_value)
        longest_uninterrupted_sequence = find_longest_uninterrupted_sequence(preceding_bullet_values)

        predictions = self.model.predict(df.parsed)
        df["prediction"] = list(predictions)

        if longest_uninterrupted_sequence is not None:
            is_question_to_include = np.zeros((len(df),), dtype=bool)
            for idx, seq_type, value in longest_uninterrupted_sequence:
                is_question_to_include[idx] = 1
            df["is_question_to_include"] = is_question_to_include
        else:
            # df["prediction"] = list(predictions)
            # df["is_question_to_include"] = df["prediction"] == 2
            df["is_question_to_include"] = df.span.apply(is_acceptable_span)

        #
        # # if no question-level options can be found
        # options = list(df[df.prediction == 1]["text"].apply(clean_options))
        # options_joined_fallback = "/".join(set(options))
        #
        # options_all_questions = []
        # for idx in range(len(df)):
        #     if df["is_question_to_include"].iloc[idx]:
        #         o = []
        #         for j in range(idx + 1, len(df)):
        #             if df["is_question_to_include"].iloc[j]:
        #                 break
        #             if df["prediction"].iloc[j] == 1:
        #                 o.append(clean_options(df.text.iloc[j]))
        #
        #         if len(o) == 0:
        #             options_this_question = options_joined_fallback
        #         else:
        #             options_this_question = "/".join(set(o))
        #
        #         options_all_questions.append(options_this_question)

        df_pred = df[df["is_question_to_include"]]
        df_pred.rename(columns={"preceding_bullet_value": "question_no"}, inplace=True)

        return df_pred
    #
    # def get_language_and_df(self, pages):
    #     text = "\n".join(pages)
    #     language = detect(text)
    #
    #     doc = process_text(text, language)
    #
    #     df = convert_to_dataframe(doc)
    #
    #     df_questions = self.get_questions(df)
    #
    #     add_candidate_options(df_questions, doc)
    #
    #     df_questions["question"] = df_questions.text.apply(clean_question)
    #     df_questions.drop(columns="text", inplace=True)
    #
    #     return language, df_questions
