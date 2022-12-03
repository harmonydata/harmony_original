import codecs
import pickle as pkl
import re

import numpy as np
from dash import Input, Output, ctx
from dash import callback_context
from dash.dependencies import State
from dash.exceptions import PreventUpdate

from dash_callbacks.cytoscape_wrapper import get_cyto_stylesheet, get_node_options_with_cytoscape_colour_scheme, \
    make_cytoscape_graph
from dash_callbacks.graph_utils import get_question_dfs, convert_similarities_into_network_graph, \
    add_manual_edges_to_generated_graph, convert_network_graph_to_dataframes
from utils.question_matcher_transformer_huggingface_negation_efficient import QuestionMatcherTransformerHuggingFaceNegationEfficient
from utils.serialisation_tools import deserialise_manual_edges, serialise_manual_edges, deserialise_questions_dataframe, \
    serialise_dataframe

question_matcher = QuestionMatcherTransformerHuggingFaceNegationEfficient()


def add_view_2_callbacks(dash_app):
    @dash_app.callback(
        output=[  # Output("paragraph_id", "children"),
            Output("similaritystore", "data"),
            Output("all_loading_messages", "style"),
            Output("dropdown-categories", "options"),
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

        matches = question_matcher.match_questions(question_dfs)

        pickled = codecs.encode(pkl.dumps(matches), "base64").decode()

        text_style = {"display": "none"}

        category_options = []
        for cat in sorted(set(df_questions.question_category)):
            category_options.append({"label": cat, "value": cat})

        return [pickled, text_style, category_options]

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
            State("excerpt_table", "columns"),
            State("excerpt_table", "data"),
            State("excerpt_table", "derived_virtual_indices"),
            State("excerpt_table", "selected_rows"),
            Input("manual_edges", "data"),
            Input("select_language", "value")
        ],
        prevent_initial_call=True
    )
    def display_similarity_graph(pickled, sensitivity, categories_to_display, columns, data, filtered_rows,
                                 selected_rows, manual_edges_serialisable, language):
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

        # start of method
        files, question_dfs = get_question_dfs(df_questions)

        G = convert_similarities_into_network_graph(question_dfs, matches, sensitivity)

        add_manual_edges_to_generated_graph(G, manual_edges)

        df_harmonised, df_harmonised_text = convert_network_graph_to_dataframes(files, question_dfs, G, _)

        # Now make the Cytoscape graph

        elements, cytoscape_layout = make_cytoscape_graph(files, question_dfs, G, df_harmonised, _)

        # Get the options
        node_options = get_node_options_with_cytoscape_colour_scheme(question_dfs)

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
