import base64
import io
import os
import pickle as pkl
import re
import time
import traceback

import dash
import flask
import pandas as pd
from dash import html, Input, Output
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from langdetect import detect
from tika import parser

from dash_callbacks.callbacks_view_2 import question_matcher
from dash_layout.body import file_to_text
from utils.excel_processor import convert_jsonified_excel_to_questions_dataframe
from utils.options_extractor import add_candidate_options
from utils.pdf_parser import parse_pdf
from utils.question_category_classifier import QuestionCategoryClassifier
from utils.question_extractor import QuestionExtractor
from utils.question_extractor import process_text, convert_to_dataframe
from utils.serialisation_tools import serialise_dataframe

COMMIT_ID = os.environ.get('COMMIT_ID', "not found")
MAX_NUMBER_OF_DOCUMENTS = 20

question_extractor = QuestionExtractor()
question_category_classifier = QuestionCategoryClassifier("models/question_category_classifier.pkl.bz2")
# question_category_classifier = QuestionCategoryClassifierTransformerHuggingFace()
# adult_child_classifier = AdultChildClassifier("models/adult_child_classifier.pkl.bz2")
# questionnaire_classifier = QuestionnaireClassifier("models/questionnaire_classifier.pkl.bz2")

# Token contains a number but may not contain exclusively a number
number_regex = re.compile(r'^(\d+)\. ')
# Token is only a pure integer number.
just_number_regex = re.compile(r'^\d+$')

re_starts_with_number = re.compile(r'^\d+[a-z]?')

# Unicode characters for all language flags featured in the app.
flags = {
    "zh": "🇨🇳",
    "es": "🇪🇸🇲🇽",
    "de": "🇩🇪",
    "ja": "🇯🇵",
    "ru": "🇷🇺",
    "it": "🇮🇹",
    "ko": "🇰🇷",
    "pt": "🇧🇷🇵🇹",
    "uk": "🇺🇦",
    "el": "🇬🇷",
    "fr": "🇫🇷",
    "en": "🇬🇧🇺🇸"
}


def get_human_readable_language(language: str) -> str:
    """
    Display language ID with a flag graphic for better readability.
    :param language: The alpha-2 code of the language.
    :return:
    """
    return flags.get(language, "") + language.upper()


def rearrange_columns(df_questions: pd.DataFrame) -> pd.DataFrame:
    """
    Move the Filename and Category columns to the beginning of the dataframe for better readability.
    :param df_questions: a dataframe to display to the user in Panel 1.
    :return: the same dataframe with columns rearranged.
    """
    cols = list(df_questions.columns)
    cols.insert(0, cols.pop(cols.index('filename')))
    cols.insert(2, cols.pop(cols.index('question_category')))
    df_questions = df_questions.loc[:, cols]
    return df_questions


def add_view_1_callbacks(dash_app):
    """
    Define all callbacks related to Tab 1 ("Upload your items").

    :param dash_app:
    :return:
    """

    @dash_app.callback(output=[Output("is_visited_before", "data")],
                       inputs=[Input("url", "href")]
                       )
    def find_if_tooltip_cookie_present(location):
        # If a cookie has been set, we don't display tooltips
        allcookies = dict(flask.request.cookies)
        if "harmony cookie" in allcookies:
            return [True]
        else:
            return [False]

    @dash_app.callback(
        output=[Output("log_tika", "children")],
        inputs=[Input("url", "href")]
    )
    def wake_up_tika_web_app_on_page_load(location):
        """
        Wake up the Tika web app the first time the page is loaded.

        This is to ensure that there is not a huge turnaround time the first time the user uploads a PDF.
        :param location: a dummy trigger just to ensure that this function is called as soon as the browser requests the URL of the app.
        :return: Some human-readable description to be displayed in a log view for diagnostics
        """
        print(f"Initialising Tika server")
        start_time = time.time()
        response = parser.from_buffer(io.BytesIO(b""), xmlContent=True)
        end_time = time.time()
        print("Initialised Tika server")

        return [
            [f"Version: {COMMIT_ID}.", html.Br(), f"Initialised server for parsing text from PDFs at {time.ctime()}.",
             html.Br(),
             f"Response was {len(str(response))} characters received in {end_time - start_time:.2f} seconds."]]

    @dash_app.callback(
        output=[  # Output("paragraph_id", "children"),
            Output("document_content", "data"),
            Output("dataset", "value"),
            Output("please_upload_message", "style"),
            Output("please_wait_message", "style"),
        ]
        ,
        inputs=[Input("file_table", "data"),  # Commented out temporarily to remove circular dependency warning
                Input("dataset", "value"),
                Input("btn_show_paste_data", "n_clicks"),
                Input('upload-data', 'contents'),
                State('upload-data', 'filename'),
                State('upload-data', 'last_modified'),
                State("document_content", "data"),
                State('paste_data_title', 'value'),
                State("paste_data", "value"),
                ],
        prevent_initial_call=True
    )
    def user_uploaded_files(file_table,
                            selected_datasets, n_clicks, all_file_contents, file_names, file_date, parsed_documents,
                            paste_data_title, paste_data):

        print("file_names", file_names)

        if parsed_documents is None:
            parsed_documents = {}

        # Commented out temporarily to remove circular dependency warning
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        # START FOR DEBUGGING
        if os.environ.get("dash_debug") and os.environ.get("dash_debug") == "True" and trigger_id == "url":
            print(all_file_contents)
            with open("debugging_file.pkl", "rb") as f:
                all_file_contents = pkl.load(f)
            file_names = ["Loaded from debug.xlsx"]
        # else:
        #     with open("debugging_file.pkl", "wb") as f:
        #         pkl.dump(all_file_contents, f)
        # END FOR DEBUGGING

        print("trigger_id", trigger_id)
        if trigger_id == "btn_show_paste_data":
            if paste_data_title is None or paste_data_title == "":
                paste_data_title = "Items"
            if not paste_data_title.lower().endswith(".txt"):
                paste_data_title += ".txt"
            parsed_documents[paste_data_title] = paste_data
            return [parsed_documents, selected_datasets, {"display": "none"}, {}]
        elif trigger_id == "file_table":
            # User deleted a row
            files_to_include = [r["File"] for r in file_table]
            print("files_to_include", files_to_include)
            got_data = set(parsed_documents)
            for file in got_data:
                if file not in files_to_include:
                    del parsed_documents[file]
            got_data = set(selected_datasets)
            for file in got_data:
                if file not in files_to_include:
                    selected_datasets.remove(file)
            if len(parsed_documents) > MAX_NUMBER_OF_DOCUMENTS:
                parsed_documents = parsed_documents[:MAX_NUMBER_OF_DOCUMENTS]
            return [parsed_documents, selected_datasets, {"display": "none"}, {}]
        elif trigger_id == "dataset":
            for preset_dataset_id in file_to_text:
                if preset_dataset_id in selected_datasets:
                    parsed_documents[preset_dataset_id] = file_to_text[preset_dataset_id]
                elif preset_dataset_id in parsed_documents:
                    del parsed_documents[preset_dataset_id]
            if len(parsed_documents) > MAX_NUMBER_OF_DOCUMENTS:
                parsed_documents = parsed_documents[:MAX_NUMBER_OF_DOCUMENTS]
            return [parsed_documents, selected_datasets, {"display": "none"}, {}]
        # elif selected_datasets is not None and len(selected_datasets) > 0:
        #     for selected_dataset in selected_datasets:
        #         parsed_documents[selected_dataset] = file_to_text[selected_dataset]
        #     if len(parsed_documents) > MAX_NUMBER_OF_DOCUMENTS:
        #         parsed_documents = parsed_documents[:MAX_NUMBER_OF_DOCUMENTS]
        #     return [parsed_documents, PLEASE_WAIT_MESSAGE]
        elif all_file_contents is not None:
            for file_name, this_file_contents in zip(file_names, all_file_contents):
                print("file_name", file_name)
                if file_name.lower().endswith("pdf"):
                    parsed_documents[file_name] = parse_pdf(this_file_contents)
                elif file_name.lower().endswith("xlsx"):
                    content_type, content_string = this_file_contents.split(",")
                    excel_as_byte_array = base64.b64decode(content_string)
                    xls_with_all_sheets = pd.ExcelFile(io.BytesIO(excel_as_byte_array))
                    for sheet_name in xls_with_all_sheets.sheet_names:
                        df = pd.read_excel(io.BytesIO(excel_as_byte_array), sheet_name=sheet_name, header=None)
                        parsed_documents[file_name + " sheet " + sheet_name] = df.to_json()
            if len(parsed_documents) > MAX_NUMBER_OF_DOCUMENTS:
                keys = reversed(list(parsed_documents))
                for k in keys:
                    del parsed_documents[k]
                    if len(parsed_documents) <= MAX_NUMBER_OF_DOCUMENTS:
                        break
            return [parsed_documents, selected_datasets, {"display": "none"}, {}]
        raise PreventUpdate

    @dash_app.callback(
        output=[  # Output("paragraph_id", "children"),
            Output("file_table", "columns"),
            Output("file_table", "data"),
        ]
        ,
        inputs=[Input("document_content", "data"),
                Input("select_language", "value"),

                ],
        prevent_initial_call=True
    )
    def display_files_list(document_content, language):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        print("trigger_id", trigger_id)
        if trigger_id == "file_table":
            return dash.no_update
            # If the original trigger of this callback was the user modifying the table listing the files, we abort the update to avoid circular dependencies.
            # Dash will still give a warning but it's nothing to worry about.

        if language == "pt":
            from application import pt_lang
            _ = pt_lang.gettext
        else:
            _ = lambda x: x

        df_file_list = pd.DataFrame()
        df_file_list["File"] = list(sorted(document_content))

        serialised_columns, serialised_data = serialise_dataframe(df_file_list, False, _)

        return [serialised_columns, serialised_data]

    @dash_app.callback(
        output=[  # Output("paragraph_id", "children"),
            Output("excerpt_table", "columns"),
            Output("excerpt_table", "data"),
            Output('excerpt_table', 'selected_rows')
        ]
        ,
        inputs=[Input("document_content", "data"),
                Input("select_language", "value"),
                Input("add_row", "n_clicks"),
                # Input("btn_filter_topic", "n_clicks"),
                State("excerpt_table", "columns"),
                State("excerpt_table", "data"),
                # State("filter_topic", "value")
                ],
        prevent_initial_call=True
    )
    def display_questions(document_content, language, add_row,  # btn_filter_topic,
                          old_cols, old_data,  # filter_topic
                          ):
        # if True:  # for debugging
        #     df_questions = pd.read_excel("../notebooks/Data (20).xlsx")
        #     return [[{"name": i, "id": i, "hideable": True} for i in df_questions.columns],
        #             df_questions.to_dict('records')]
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "add_row":
            old_data.append({c['id']: '' for c in old_cols})
            return [old_cols, old_data, list(range(len(old_data)))]

        if language == "pt":
            from application import pt_lang
            _ = pt_lang.gettext
        else:
            _ = lambda x: x

        dfs = []

        for file_name, pages in document_content.items():
            if file_name.endswith("txt"):
                text = pages
                language = detect(text)

                df_questions = pd.DataFrame()

                question_texts = text.split("\n")
                question_texts = [q.strip() for q in question_texts if len(q.strip()) > 0]
                question_numbers = [str(i + 1) for i in range(len(question_texts))]
                question_options = [""] * len(question_texts)

                for idx, q in enumerate(question_texts):
                    m = re_starts_with_number.match(q)
                    if m:
                        question_numbers[idx] = m.group()
                        question_texts[idx] = re.sub(r'^' + m.group() + r'[\.\s\)]+', "", q)
                    else:
                        question_texts[idx] = q

                    colon = re.split(":|\t", question_texts[idx])
                    if len(colon) > 1:
                        question_options[idx] = colon[1]
                        question_texts[idx] = colon[0]

                df_questions = pd.DataFrame()
                df_questions["question_no"] = question_numbers
                df_questions["question"] = question_texts
                df_questions["options"] = question_options

                df_questions["filename"] = file_name
                df_questions["language"] = get_human_readable_language(language)
                df_questions.attrs["language"] = language
            elif file_name.endswith("pdf"):
                text = "\n".join(pages)
                language = detect(text)
                doc = process_text(text, language)
                df = convert_to_dataframe(doc)
                df_questions = question_extractor.get_questions(df)
                add_candidate_options(df_questions, doc)

                df_questions = df_questions[["question_no", "question", "options"]]

                df_questions["filename"] = file_name
                df_questions["language"] = get_human_readable_language(language)
                df_questions.attrs["language"] = language
            else:
                df_questions = convert_jsonified_excel_to_questions_dataframe(pages)
                language = "en"
                try:
                    language = detect(" ".join(df_questions["question"]))
                except:
                    print("Error identifying language in Excel file")
                    traceback.print_exc()
                    traceback.print_stack()

                if "filename" not in df_questions.columns:
                    df_questions["filename"] = file_name
                if "language" not in df_questions.columns:
                    df_questions["language"] = get_human_readable_language(language)
                df_questions.attrs["language"] = language

            # broken broken broken
            # df_questions["question"] = df_questions.text.apply(clean_question)
            # drop the unnecessary columns

            # this is not very good atm
            # df_questions.attrs["category"] = questionnaire_classifier.categorise_questionnaire(text, language)
            # df_questions["category"] = df_questions.attrs["category"]
            # this is not very good atm
            # question_category_classifier.categorise_questions(df_questions)

            # this is also not very good atm
            # adult_child_classifier.categorise_age_group(df_questions)
            # df_questions["age_group"] = df_questions.attrs["age"]

            dfs.append(df_questions)

        if len(dfs) > 0:
            df_questions = pd.concat(dfs)
        else:
            df_questions = pd.DataFrame(
                {"question_no": [], "question": [], "options": [], "filename": [], "language": []})

        question_category_classifier.categorise_questions(df_questions)

        df_questions = rearrange_columns(df_questions)

        #
        # if filter_topic is not None and filter_topic != "":
        #     try:
        #         question_dfs = []
        #         question_dfs.append(pd.DataFrame({"question":[filter_topic]}))
        #         question_dfs.append(df_questions)
        #         matches = question_matcher.match_questions(question_dfs, is_use_cosine_similarity=True)
        #         similarities = []
        #         for idx in range(len(df_questions)):
        #             similarities.append(matches.get((0,0,1,idx)))
        #         df_questions["similarity"] = similarities
        #         df_questions["abs_similarity"] = df_questions["similarity"].apply(abs)
        #         df_questions.sort_values("abs_similarity", inplace=True, ascending=False)
        #
        #         df_questions.drop(columns=["parsed", "parsed_neg", "normalised", "similarity", "abs_similarity"], inplace=True)
        #     except:
        #         print("Error filtering")
        #         traceback.print_exc()
        #         traceback.print_stack()

        df_questions["id"] = [int(i) for i in range(len(df_questions))]

        serialised_columns, serialised_data = serialise_dataframe(df_questions, True, _)

        import json
        print(json.dumps(serialised_columns, ensure_ascii=False, indent=4))

        return [serialised_columns,
                serialised_data, list(range(len(serialised_data)))]

    @dash_app.callback(
        output=[  # Output("paragraph_id", "children"),
            Output("excerpt_table", "filter_query"),
        ]
        ,
        inputs=[Input("filter_questions", "value"),
                Input("btn_filter_topic", "n_clicks"),
                State("filter_topic", "value"),
                State("filter_topic_threshold", "value"),
                State("excerpt_table", "data"),
                ],
        prevent_initial_call=True
    )
    def update_filter_query(document_content, n_clicks, filter_topic, filter_topic_threshold, data
                            ):
        ctx = dash.callback_context
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if trigger_id == "filter_questions":
            if document_content is not None and document_content != "":
                return ["{filename} = '" + document_content + "'"]

        if trigger_id == "btn_filter_topic" and filter_topic is not None and filter_topic != "":
            question_dfs = []
            question_dfs.append(pd.DataFrame({"question": [filter_topic]}))
            questions2 = pd.DataFrame()
            questions2["question"] = [x["question"] for x in data]
            questions2["id"] = [x["id"] for x in data]
            question_dfs.append(questions2)
            matches = question_matcher.match_questions(question_dfs, is_use_cosine_similarity=True)
            ids = []
            for idx in range(len(questions2)):
                m = matches.get((0, 0, 1, idx))
                if m and m > filter_topic_threshold:
                    ids.append(questions2["id"].iloc[idx])

            query = " or ".join(["{id} = " + str(id) for id in ids])

            return [query]

        return [""]

    # @dash_app.callback(
    #     output=[  # Output("paragraph_id", "children"),
    #         Output("excerpt_table", "derived_virtual_indices"),
    #     ]
    #     ,
    #     inputs=[
    #             Input("btn_filter_topic", "n_clicks"),
    #             State("excerpt_table", "data"),
    #             State("filter_topic", "value")
    #             ],
    #     prevent_initial_call=True
    # )
    # def update_filter_query(n_clicks,data, filter_topic):
    #
    #     return [[0,1,2]]

    @dash_app.callback(
        output=[
            Output("filter_questions", "options"),
        ]
        ,
        inputs=[Input("excerpt_table", "data"),
                ],
        prevent_initial_call=True
    )
    def update_filter_options(data):
        filenames = sorted(set([r['filename'] for r in data]))
        return [[{"value": f, "label": f} for f in filenames]]
