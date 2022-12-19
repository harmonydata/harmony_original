from IPython.display import display, HTML
import bz2
import os
import pickle as pkl
import re
import sys
from nltk.corpus import stopwords
from langdetect import detect
import numpy as np
import operator 
import pandas as pd
import sklearn.metrics as metrics
import matplotlib.pyplot as plt

from utils.spacy_wrapper import get_spacy_model

pd.set_option("max_colwidth", None)
pd.set_option("max_seq_items", None)


def validate(validation_data, match_function, MODEL_NAME):
    for dataset, dataset_data in validation_data.items():
        print (f"Validating on dataset {dataset}")
        question_dfs = []
        for questionnaire in dataset_data:
            df = pd.DataFrame({"question": [q for q, c, n in questionnaire]})
            df.attrs['language'] = "en"
            if "PT" in dataset or "Sentir" in questionnaire[0][0]:
                df.attrs['language'] = "pt"
                print ("Found Portuguese dataset", dataset)
            question_dfs.append(df)

        print (f"\tProcessing {len(question_dfs)} instruments of average length {int(np.round(np.mean([len(d) for d in question_dfs])))} questions each")
        matches = match_function(question_dfs)

        print (f"\tCalculated {len(matches)} match scores")

        pairs_already_seen = set()
        gold_standard = {}
        for i in range(len(dataset_data)):
            for j in range(i + 1, len(dataset_data)):
                for ii in range(len(dataset_data[i])):
                    for jj in range(len(dataset_data[j])):
                        tup = tuple(sorted([dataset_data[i][ii][2], dataset_data[j][jj][2]]))
                        if tup not in pairs_already_seen:
                            gold_standard[(i, ii, j, jj)] = int(
                                (dataset_data[i][ii][1] == dataset_data[j][jj][1])
                                or 
                                (dataset_data[i][ii][2] == dataset_data[j][jj][2])
                            )
                        pairs_already_seen.add(tup)

        print (f"\tGenerated {len(gold_standard)} gold-standard values to compare them to")

        print ("\tCalculating ROC curve")

        y_pred = []
        y_test = []
        for m, g in gold_standard.items():
            y_pred.append(abs(matches.get(m, 0)))
            y_test.append(g)

        fpr, tpr, threshold = metrics.roc_curve(y_test, y_pred)
        roc_auc = metrics.auc(fpr, tpr)

        plt.plot(fpr, tpr, label = f'AUC = {roc_auc:0.2f} {dataset}')

        print (f"\nFALSE NEGATIVES OR WEAKEST MATCHES {dataset}\n")

        all_positives = [m for m in gold_standard if gold_standard[m] == 1 ]
        estimated_values_for_gt_1 = dict([(m,abs(matches[m])) for m in all_positives ])

        ctr = 0    
        examples = []
        for match_tuple, score_from_model in sorted(estimated_values_for_gt_1.items(), key=operator.itemgetter(1)):
            examples.append((question_dfs[match_tuple[0]].question.iloc[match_tuple[1]], question_dfs[match_tuple[2]].question.iloc[match_tuple[3]], np.round(score_from_model, 2)))

            ctr += 1
            if ctr > 10:
                break
        df_examples = pd.DataFrame({"Instrument 1":[e[0] for e in examples],"Instrument 2":[e[1] for e in examples],"Score from model":[e[2] for e in examples]})
        df_examples["Ground truth"] = 1
        display(df_examples)


        print (f"\nFALSE POSITIVES OR WEAKEST REJECTIONS {dataset}\n")

        all_negatives = [m for m in gold_standard if gold_standard[m] == 0 ]
        estimated_values_for_gt_1 = dict([(m,abs(matches[m])) for m in all_negatives ])

        ctr = 0
        examples = []
        for match_tuple, score_from_model in sorted(estimated_values_for_gt_1.items(), key=operator.itemgetter(1), reverse=True):
            examples.append((question_dfs[match_tuple[0]].question.iloc[match_tuple[1]], question_dfs[match_tuple[2]].question.iloc[match_tuple[3]], np.round(score_from_model, 2)))

            ctr += 1
            if ctr > 10:
                break
        df_examples = pd.DataFrame({"Instrument 1":[e[0] for e in examples],"Instrument 2":[e[1] for e in examples],"Score from model":[e[2] for e in examples]})
        df_examples["Ground truth"] = 0
        display(df_examples)


    plt.title(f'Receiver Operating Characteristic\n{MODEL_NAME}\nEvaluated on harmonisation tool McElroy et al (2020)\nand English vs Portuguese GAD-7')
    plt.legend(loc = 'lower right')
    plt.plot([0, 1], [0, 1],'--', color='black', alpha=0.5)
    plt.xlim([-0.01, 1.01])
    plt.ylim([-0.01, 1.01])
    plt.ylabel('True Positive Rate')
    plt.xlabel('False Positive Rate')
    plt.show()