import os

file_name = os.path.join(os.path.dirname(__file__), '../models/pt_en_map.csv')

pt_en_map = {}
with open(file_name, "r", encoding="utf-8") as f:
    for l in f:
        pt, en = l.strip().split("\t")
        pt_en_map[pt] = en
