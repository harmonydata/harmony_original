import pandas as pd

INPUT_FILE = "../data/BHRCS_SDQ_CBCL_harmonization.xlsx"

df_harmonised = pd.read_excel(INPUT_FILE, sheet_name="1_by_n")
df_sdq = pd.read_excel(INPUT_FILE, sheet_name="Complete SDQ")
df_cbcl = pd.read_excel(INPUT_FILE, sheet_name="Complete CBCL")

mapping = {}
i2 = None
for idx in range(1, len(df_harmonised)):
    i1 = df_harmonised["CBCL"].iloc[idx]
    new_i2 = df_harmonised['Unnamed: 2'].iloc[idx]
    
    if not pd.isna(new_i2):
        i2 = new_i2
    
    mapping[i2] = i1

validation_data_bhrcs = [[], []]

for i in range(len(df_cbcl)):
    t = df_cbcl["Conteúdo"].iloc[i]
    if type(t) is str:
        validation_data_bhrcs[0].append((t.strip(), df_cbcl["Item"].iloc[i]))

for i in range(len(df_sdq)):
    t = df_cbcl["Conteúdo"].iloc[i]
    if type(t) is str:
        cbcl_id = "CB" + df_cbcl["Item"].iloc[i]
        sdq_id = mapping.get(cbcl_id, cbcl_id)
        validation_data_bhrcs[1].append((t.strip(), sdq_id))