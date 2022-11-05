import operator
from collections import Counter

import numpy as np

from utils.spacy_wrapper import get_spacy_model
from utils.stopwords_psych import PSYCH_STOPWORDS


def get_keywords_for_groups(list_of_lists_of_texts: list) -> list:
    """
    Given a set of grouped questions, this identifies the key words that can be used to summarise each group.
    :param list_of_lists_of_texts:
    :return:
    """
    nlp_en = get_spacy_model("en")
    nlp_pt = get_spacy_model("pt")
    stopwords = PSYCH_STOPWORDS

    keywords_found = [""] * len(list_of_lists_of_texts)

    list_of_lists_of_docs = []
    for list_of_texts in list_of_lists_of_texts:
        docs = list(nlp_en.pipe(list_of_texts))
        list_of_lists_of_docs.append(docs)

    counter_over_all_groups = Counter()
    group_specific_counters = []

    for docs in list_of_lists_of_docs:
        counter = Counter()
        for doc in docs:
            for token in doc:
                if token.is_alpha:
                    token_lemma = token.lemma_.lower()
                    if token_lemma not in stopwords:
                        counter_over_all_groups[token_lemma] += 1
                        counter[token_lemma] += 1
        group_specific_counters.append(counter)

    top_words = []

    for group_idx, counter in enumerate(group_specific_counters):
        words_to_tfidfs = {}
        for word in counter:
            tf = counter[word]
            idf = np.log(sum(counter_over_all_groups.values()) / counter_over_all_groups[word])
            tf_idf = tf * idf
            words_to_tfidfs[word] = tf_idf

        top_words.append(sorted(words_to_tfidfs.items(), key=operator.itemgetter(1), reverse=True))

    counter_for_which_words_are_at_the_top_of_at_least_one_group = Counter()
    for idx, top_words_list in enumerate(top_words):
        if len(top_words_list) > 0:
            counter_for_which_words_are_at_the_top_of_at_least_one_group[top_words_list[0][0]] += 1

    for word, count in counter_for_which_words_are_at_the_top_of_at_least_one_group.items():
        if count > 1:
            for idx, top_words_list in enumerate(top_words):
                if len(top_words_list) > 0:
                    if top_words_list[0][0] == word:
                        top_words_list.pop()

    for group_idx, top_words_list in enumerate(top_words):
        if len(top_words_list) > 0:
            keywords_found[group_idx] = top_words_list[0][0]

    return keywords_found
