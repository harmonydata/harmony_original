import os
import pickle as pkl
import re
import bz2

import pandas as pd

input_folder = "hard_coded_questionnaires"
file_to_text = {}
for root, folder, files in os.walk(input_folder):
    for file_name in files:
        if not file_name.endswith("csv"):
            continue

        full_file = input_folder + "/" + file_name

        with open(full_file, 'rb') as f:
            df = pd.read_csv(full_file, encoding="utf-8", sep="\t")
        file_to_text[re.sub(r'.csv', '', file_name)] = df.to_json()

with bz2.open(input_folder + "/questionnaires.pkl.bz2", "wb") as f:
    pkl.dump(file_to_text, f)
