import pandas as pd
import re

INPUT_FILE = "../data/Final harmonised item tool EM.xlsx"

validation_data = {}

for sheet_name in ("Childhood","Adulthood"):

    df = pd.read_excel(INPUT_FILE, sheet_name=sheet_name)

    if sheet_name == "Adulthood":
        labels_in_this_sheet = ["Adulthood"] * len(df)
        df = df[df.columns[4:]]
    else:
        labels_in_this_sheet = list(df["Developmental period"])
        df = df[df.columns[5:]]

    all_questions = []
    category_to_id = {}
    for idx in range(0, len(df)):
        questions_in_survey = []
        for column in df.columns:
            cell_content = df[column].iloc[idx]
            if type(cell_content) is str:
                cell_content = re.sub("tiredness/exhaustion", "tiredness or exhaustion", cell_content)
                for text in cell_content.split("/"):
                    text = re.sub(r'[^A-Za-z -,]', '', text.strip()).strip()
                    category = column.strip()
                    if category not in category_to_id:
                        category_to_id[category] = len(category_to_id)
                    category_id = category_to_id[category]
                    if len(text) > 2:
                        
                        questions_in_survey.append((text, category_id))
        all_questions.append(questions_in_survey)
    
    validation_data[sheet_name] = all_questions
    
validation_data_mcelroy_childhood, validation_data_mcelroy_adulthood = validation_data["Childhood"], validation_data["Adulthood"]