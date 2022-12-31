import codecs
import pickle as pkl
import re

import numpy as np
import pandas as pd
from dash import Input, Output, ctx
from dash import callback_context
from dash.dependencies import State
from dash.exceptions import PreventUpdate
from sklearn.manifold import TSNE

from dash_callbacks.cytoscape_wrapper import get_cyto_stylesheet, get_node_options_with_cytoscape_colour_scheme, \
    make_cytoscape_graph
from dash_callbacks.graph_utils import get_question_dfs, convert_similarities_into_network_graph, \
    add_manual_edges_to_generated_graph, convert_network_graph_to_dataframes, get_text_of_question, \
    get_number_of_question
from utils.question_matcher_transformer_huggingface_negation_efficient import \
    QuestionMatcherTransformerHuggingFaceNegationEfficient
from utils.serialisation_tools import deserialise_manual_edges, serialise_manual_edges, deserialise_questions_dataframe, \
    serialise_dataframe

question_matcher = QuestionMatcherTransformerHuggingFaceNegationEfficient(
    'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')


# from utils.question_matcher_nonpretrained import QuestionMatcherNonpretrained
# question_matcher = QuestionMatcherNonpretrained()

def add_view_2_callbacks(dash_app):
    @dash_app.callback(
        output=[  # Output("paragraph_id", "children"),
            Output("similaritystore", "data"),
            Output("all_loading_messages", "style"),
            Output("dropdown-categories", "options"),
            Output("dropdown-files", "options"),
            Output("document_vectors", "data"),
        ]
        ,
        inputs=[
            Input("btn_calculate_match", "n_clicks"),
            Input("tabs", "value"),
            State("excerpt_table", "columns"),
            State("excerpt_table", "data"),
            State("excerpt_table", "derived_virtual_indices"),
            State("excerpt_table", "selected_rows"),
            State("similaritystore", "data"),
        ],
    )
    def find_similarity(_, tab, columns, data, filtered_rows, selected_rows, old_similarity_store):
        print("SEL", selected_rows)
        """
        This function does the heavy lifting.

        :param _:
        :param tab:
        :param columns:
        :param data:
        :param old_similarity_store:
        :return:
        """
        # if this was triggered by the tab, only run the calculation if it's the first time.
        # TODO- have commented this out for better UX
        # if ctx.triggered_id == "tabs" and old_similarity_store is not None:
        #     raise PreventUpdate

        callback_context.response.set_cookie('harmony cookie', '1')

        # If user has selected some rows with the checkbox, use only them.
        if selected_rows is not None and len(selected_rows) > 0:
            data = [data[r] for r in selected_rows]
        # elif filtered_rows is not None and len(filtered_rows) > 0:
        #     data = [data[r] for r in filtered_rows]

        df_questions = deserialise_questions_dataframe(columns, data)

        # start of method
        files, question_dfs = get_question_dfs(df_questions)

        matches = question_matcher.match_questions(question_dfs, is_use_cosine_similarity=True)

        pickled = codecs.encode(pkl.dumps(matches), "base64").decode()

        text_style = {"display": "none"}

        category_options = []
        for cat in sorted(set(df_questions.question_category)):
            category_options.append({"label": cat, "value": cat})

        file_options = []
        for f in sorted(set(df_questions.filename)):
            file_options.append({"label": f, "value": f})

        serialisable_document_vectors = []
        for question_df_idx, df in enumerate(question_dfs):
            for j in range(len(df)):
                serialisable_document_vectors.append([str((question_df_idx, j)), [float(x) for x in df.vector.iloc[j]]])

        return [pickled, text_style, category_options, file_options, serialisable_document_vectors]

    @dash_app.callback([
        Output("dropdown-selected", "value"),
    ],
        [Input('cytoscape-update-layout', 'mouseoverEdgeData'),
         Input('cytoscape-update-layout', 'tapNodeData'),
         State("dropdown-selected", "value")],
        prevent_initial_callback=True)
    def user_clicks_node_or_moves_over_edge(mouseover_edge_data, tap_node_data, orig_selection):
        # print("USERCLICKSGRAPH", mouseover_edge_data, tap_node_data, orig_selection)
        if mouseover_edge_data:
            if 'source' in mouseover_edge_data:
                return [[mouseover_edge_data['source'], mouseover_edge_data['target']],
                        ]
        if tap_node_data:
            if orig_selection is None:
                orig_selection = []
            # Don't allow user to select more than two nodes
            if len(orig_selection) > 1:
                orig_selection = orig_selection[:1]
            # Don't allow user to select two nodes from same file
            if len(orig_selection) == 1 and orig_selection[0][:2] == tap_node_data['id'][:2]:
                orig_selection = []
            if tap_node_data['id'].startswith("("):
                orig_selection.append(tap_node_data['id'])
                print("Selection is", orig_selection)
                return [orig_selection]
        raise PreventUpdate

    @dash_app.callback([
        Output("manual_edges", "data"),
    ],
        [Input('btn_update_edge', 'n_clicks'),
         Input("btn_clear_edge", "n_clicks"),
         State("dropdown-selected", "value"),
         State("dropdown-edge", "value"),
         State("manual_edges", "data")],
        prevent_initial_callback=True)
    def user_updates_edge(_, __, selected_pair, value, manual_edges_serialisable):
        if ctx.triggered_id == "btn_clear_edge":
            return [{}]
        # print("selected_pair", selected_pair)
        # print(f"manual_edges_serialisable received {manual_edges_serialisable}")
        manual_edges = deserialise_manual_edges(manual_edges_serialisable)

        if len(selected_pair) == 2:
            node_1 = tuple([int(x) for x in re.sub(r'[^\d,]', '', selected_pair[0]).split(",")])
            node_2 = tuple([int(x) for x in re.sub(r'[^\d,]', '', selected_pair[1]).split(",")])
            # can't add an edge within the same file
            if node_1[0] == node_2[0]:
                raise PreventUpdate
            node_1, node_2 = sorted([node_1, node_2])
            key = (node_1, node_2)
            manual_edges[key] = float(value)
        print(f"manual_edges {manual_edges}")
        manual_edges_serialisable = serialise_manual_edges(manual_edges)
        print(f"manual_edges_serialisable output {manual_edges_serialisable}")
        return [manual_edges_serialisable]

    @dash_app.callback([
        Output("dropdown-edge", "value"),
    ],
        [Input('dropdown-selected', 'value'),
         State("cytoscape-update-layout", "elements")],
        prevent_initial_callback=True)
    def display_value_of_edge(selection, elements):
        if len(selection) == 2:
            for element in elements:
                if "source" in element["data"]:
                    if (element["data"]["source"] == selection[0] and element["data"]["target"] == selection[1]) \
                            or \
                            (element["data"]["source"] == selection[1] and element["data"]["target"] == selection[0]):
                        return [int(np.sign(element["data"]["myWidth"]))]

    @dash_app.callback(
        output=[  # Output("paragraph_id", "children"),
            Output("results_table", "columns"),
            Output("results_table", "data"),
            Output("cytoscape-update-layout", "elements"),
            Output("cytoscape-update-layout", "layout"),
            Output("dropdown-selected", "options"),
            Output("box_graph_controls", "style")
            # we make the control panel visible once the graph has been displayed once
        ]
        ,
        inputs=[
            Input("similaritystore", "data"),
            Input("my-slider", "value"),
            Input("dropdown-categories", "value"),
            Input("dropdown-files", "value"),
            Input("manual_edges", "data"),
            Input("select_language", "value"),
            Input("dropdown_table_orientation", "value"),
            # Input("dropdown_display_style", "value"),
            State("excerpt_table", "columns"),
            State("excerpt_table", "data"),
            State("excerpt_table", "derived_virtual_indices"),
            State("excerpt_table", "selected_rows"),
            State("document_vectors", "data")
        ],
        prevent_initial_call=True
    )
    def display_similarity_graph(pickled, sensitivity, categories_to_display, files_to_display,
                                 manual_edges_serialisable, language, table_orientation,  # display_style,
                                 columns, data,
                                 filtered_rows,
                                 selected_rows,
                                 document_vectors):
        if language == "pt":
            from application import pt_lang
            _ = pt_lang.gettext
        else:
            _ = lambda x: x

        # If user has selected some rows with the checkbox, use only them.
        if selected_rows is not None and len(selected_rows) > 0:
            data = [data[r] for r in selected_rows]
        # elif filtered_rows is not None and len(filtered_rows) > 0:
        #     data = [data[r] for r in filtered_rows]

        matches = pkl.loads(codecs.decode(pickled.encode(), "base64"))

        df_questions = deserialise_questions_dataframe(columns, data)

        manual_edges = deserialise_manual_edges(manual_edges_serialisable)

        if categories_to_display is not None and len(categories_to_display) > 0:
            df_questions["is_include"] = df_questions.question_category.isin(categories_to_display)
        else:
            df_questions["is_include"] = True

        if files_to_display is not None and len(files_to_display) > 0:
            df_questions["is_include"] = df_questions["is_include"] & df_questions["filename"].isin(files_to_display)

        # start of method
        files, question_dfs = get_question_dfs(df_questions)

        num_different_files = len(files)

        G = convert_similarities_into_network_graph(question_dfs, matches, sensitivity, num_different_files == 1,
                                                    num_different_files == 1)

        add_manual_edges_to_generated_graph(G, manual_edges)

        df_harmonised, df_harmonised_text = convert_network_graph_to_dataframes(files, question_dfs, G, _)

        # Now make the Cytoscape graph

        elements, cytoscape_layout = make_cytoscape_graph(files, question_dfs, G, df_harmonised, _)

        if num_different_files == 1:
            # Override the positions with a TSNE-derived set of coordinates.
            ## TSNE
            tsne = TSNE(n_components=2, verbose=1, random_state=123)

            document_vector_values = np.asarray([x[1] for x in document_vectors])
            document_vector_keys = [x[0] for x in document_vectors]

            z = tsne.fit_transform(document_vector_values)

            # Delete the parent nodes as outgoing links from child nodes
            parents = set()
            for e in elements:
                if "parent" in e:
                    parents.add(e['parent'])
                    del e["parent"]

            # Remove all the parent nodes from the graph
            elements = [e for e in elements if "data" not in e or "(" in e["data"].get("id", "(")]
            # print ("ELEMENTS", json.dumps(elements, indent=4))

            # Scale everything to keep the same scale
            min_x = min([x['x'] for x in cytoscape_layout["positions"].values()])
            max_x = max([x['x'] for x in cytoscape_layout["positions"].values()])
            min_y = min([x['y'] for x in cytoscape_layout["positions"].values()])
            max_y = max([x['y'] for x in cytoscape_layout["positions"].values()])

            min_x_tsne = min(z[:, 0])
            max_x_tsne = max(z[:, 0])

            min_y_tsne = min(z[:, 1])
            max_y_tsne = max(z[:, 1])

            if max_x_tsne > min_x_tsne and max_y_tsne > min_y_tsne:
                x_scale = (max_x - min_x) / (max_x_tsne - min_x_tsne)
                y_scale = (max_y - min_y) / (max_y_tsne - min_y_tsne)
            else:
                x_scale = 10
                y_scale = 10

            z *= np.mean([x_scale, y_scale])
            z[:, 0] = z[:, 0] * 4  # stretch in x-dimension

            for idx in range(len(document_vectors)):
                cytoscape_layout["positions"][document_vector_keys[idx]] = {"x": float(z[idx][0]),
                                                                            "y": float(z[idx][1])}

            ### END TSNE

        # Get the options
        node_options = get_node_options_with_cytoscape_colour_scheme(question_dfs)

        if table_orientation == "v":
            df_harmonised_text = df_harmonised_text.transpose()
        elif table_orientation == "m":
            # build a matrix
            axes = sorted([node for node, attr in G.nodes.items()])
            print("axes", axes, type(axes), type(axes[0]))
            values = np.zeros((len(axes), len(axes)))
            for m, v in matches.items():
                print("m is", m, type(m))
                k1 = tuple(m[:2])
                k2 = tuple(m[2:])
                x = axes.index(k1)
                y = axes.index(k2)

                values[x, y] = v
                values[y, x] = v
            df_harmonised_text = pd.DataFrame()
            df_harmonised_text["filename"] = [files[a[0]] for a in axes]
            df_harmonised_text["question_no"] = [get_number_of_question(question_dfs, a) for a in axes]
            df_harmonised_text["question"] = [get_text_of_question(question_dfs, a) for a in axes]
            for idx, a in enumerate(axes):
                v = []
                for x in values[idx, :]:
                    if x != 0:
                        v.append(str(x))
                    else:
                        v.append("")
                df_harmonised_text[get_text_of_question(question_dfs, a)] = v

        serialised_columns, serialised_data = serialise_dataframe(df_harmonised_text, False)

        button_style = {"display": "block"}
        return [serialised_columns,
                serialised_data, elements, cytoscape_layout, node_options, button_style]

    @dash_app.callback(
        output=[  # Output("paragraph_id", "children"),
            Output("cytoscape-update-layout", "stylesheet"),
        ]
        ,
        inputs=[
            Input('url', 'pathname'),
        ],
    )
    def generate_stylesheet(_):
        return [get_cyto_stylesheet()]

    @dash_app.callback(
        output=[  # Output("paragraph_id", "children"),
            Output("cytoscape-update-layout", "generateImage"),
        ]
        ,
        inputs=[
            Input("btn_save_graph", "n_clicks"),
        ],
        prevent_initial_call=True
    )
    def save_graph(_):
        return [{
            'type': "png",
            'action': "download"
        }]
