from tika import parser
import os
import pickle as pkl

from lxml import html
from tika import parser

input_folder = "raw_pdf/"
output_folder = "preprocessed_pkl"
output_folder_text = "preprocessed_text"

try:
    os.stat(input_folder)
except:
    print("Please place the questionnaire PDFs in ", input_folder)

try:
    os.stat(output_folder)
except:
    os.mkdir(output_folder)
try:
    os.stat(output_folder_text)
except:
    os.mkdir(output_folder_text)


def extract_text_from_pdf(file_path):
    parsed = parser.from_file(file_path, xmlContent=True)
    parsed_xml = parsed["content"]

    et = html.fromstring(parsed_xml)
    pages = et.getchildren()[1].getchildren()

    return [str(page.text_content()) for page in pages]


for root, folder, files in os.walk(input_folder):
    for file_name in files:
        if not file_name.endswith("pdf"):
            continue
        full_file = root + "/" + file_name
        print(full_file)

        try:
            texts = extract_text_from_pdf(full_file)
        except:
            print("Error processing", full_file, ". Skipping")
            continue
        output_file = output_folder + "/" + file_name + ".pkl"

        with open(output_file, 'wb') as fo:
            pkl.dump(texts, fo)

        output_file = output_folder_text + "/" + file_name + ".txt"
        with open(output_file, 'w', encoding="utf-8") as fo:
            for t in texts:
                fo.write(t + "\n")
