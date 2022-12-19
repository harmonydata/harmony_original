import re
import traceback

def normalise_question(original_text: str):
    """
    Checks if two questions have identical text.
    This is because they are by definition equivalent even if they are in different columns in the harmonisation tool by McElroy et al.
    """
    return re.sub(r'\W', '', original_text.lower())

def add_normalised_string(lst):
    lst2 = []
    for sublist in lst:
        lst2.append([(t, c, normalise_question(t)) for t, c in sublist])
    return lst2

validation_data = {}

from dataset_mcelroy import validation_data_mcelroy_childhood, validation_data_mcelroy_adulthood
validation_data["McElroy et al Childhood"] = add_normalised_string(validation_data_mcelroy_childhood)
validation_data["McElroy et al Adulthood"] = add_normalised_string(validation_data_mcelroy_adulthood)
from dataset_gad7_en_pt import validation_data_gad_7
validation_data["GAD-7 (EN/PT)"] = add_normalised_string(validation_data_gad_7)

try:
    from dataset_bhrcs_sdq_cbcl import validation_data_bhrcs
    validation_data["BHRCS SDQ/CBCL (PT)"] = add_normalised_string(validation_data_bhrcs)
except:
    print ("BHRCS data not available. This was not included in the repository due to copyright restrictions.")
    traceback.print_stack()