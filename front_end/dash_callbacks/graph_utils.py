import networkx as nx
import numpy as np
import pandas as pd

from utils.language_utils import get_clean_language_code
from utils.topic_identifier import get_keywords_for_groups


def get_text_of_question(question_dfs: list, node: tuple) -> str:
    if node is None:
        return ""
    return question_dfs[node[0]].question.iloc[node[1]]


def get_number_of_question(question_dfs: list, node: tuple) -> str:
    if node is None:
        return ""
    number = question_dfs[node[0]].question_no.iloc[node[1]]
    if number is None or number == "":
        return ""
    return str(number) + ". "


def get_options_of_question(question_dfs: list, node: tuple) -> str:
    if node is None:
        return ""
    return question_dfs[node[0]].options.iloc[node[1]]


def convert_network_graph_to_dataframes(files: list, question_dfs: list, G: nx.Graph, _) -> list:
    weight_lookup = nx.get_edge_attributes(G, 'weight')

    def get_importance_of_connected_component(set_of_nodes):
        component_size = len(set_of_nodes)

        nodes_list = list(set_of_nodes)
        weights = []
        for i in range(len(nodes_list)):
            for j in range(i + 1, len(nodes_list)):
                node_pair = (nodes_list[i], nodes_list[j])
                reverse_node_pair = (nodes_list[j], nodes_list[i])
                w = 0
                if node_pair in weight_lookup:
                    w = weight_lookup[node_pair]
                elif reverse_node_pair in weight_lookup:
                    w = weight_lookup[reverse_node_pair]
                weights.append(w)

        if len(weights) > 0:
            return component_size + np.mean(weights) / 1000

        return component_size

    questions_found = []

    for node_group in sorted(nx.connected_components(G), key=get_importance_of_connected_component, reverse=True):
        question_row = []
        for questionnaire_no in range(len(question_dfs)):
            question_row.append([])

        for node in node_group:
            question_row[node[0]].append(node)

        max_length = max([len(q) for q in question_row])
        for i in range(max_length):
            this_row = []
            for questionnaire_no in range(len(question_dfs)):
                cell = None
                if i < len(question_row[questionnaire_no]):
                    cell = question_row[questionnaire_no][i]
                this_row.append(cell)
            questions_found.append(this_row)

    '''
    # Align the matches into rows
    already_included = set()
    questions_found = []
    for node, attr in G.nodes.items():
        if node in already_included:
            continue

        question_row = [None] * len(question_dfs)

        question_row[node[0]] = node
        for neighbour in G.neighbors(node):
            if neighbour in already_included:
                continue
            if question_row[neighbour[0]] is not None:
                continue
            question_row[neighbour[0]] = neighbour
            already_included.add(neighbour)

        questions_found.append(question_row)
    '''

    # Make a dataframe for the harmonised questions
    df_harmonised = pd.DataFrame()
    for idx, q in enumerate(questions_found):
        df_harmonised[str(idx)] = q

    # A text version of the same dataframe
    df_harmonised_text = pd.DataFrame()

    files_to_display = []
    subheadings_to_display = []
    languages_to_display = []
    for file_idx, f in enumerate(files):
        files_to_display.append(f)
        files_to_display.append(f)
        files_to_display.append(f)
        files_to_display.append(f)
        subheadings_to_display.append(_("question numbers"))
        subheadings_to_display.append(_("questions"))
        subheadings_to_display.append(_("options"))
        subheadings_to_display.append(_("match"))
        languages_to_display.append(question_dfs[file_idx]["language"].iloc[0])
        languages_to_display.append("")
        languages_to_display.append("")
        languages_to_display.append("")
    df_harmonised_text[_("Filename")] = files_to_display
    df_harmonised_text[_("Field")] = subheadings_to_display
    df_harmonised_text[_("Language")] = languages_to_display

    list_of_lists_of_texts = []
    for idx, q in enumerate(questions_found):
        this_q_variants = []
        texts_for_topic_extraction = []
        list_of_lists_of_texts.append(texts_for_topic_extraction)
        for j in range(len(df_harmonised)):
            node = df_harmonised[str(idx)].iloc[j]
            this_q_variants.append(get_number_of_question(question_dfs, node))
            question_text = get_text_of_question(question_dfs, node)
            this_q_variants.append(question_text)
            this_q_variants.append(get_options_of_question(question_dfs, node))
            # Get match to other ndoes
            best_match = 0
            for k in range(len(df_harmonised)):
                if k == j:
                    continue
                comparison_node = df_harmonised[str(idx)].iloc[k]
                edge_data = G.get_edge_data(comparison_node, node)
                if edge_data is not None and "weight" in edge_data:
                    this_match = edge_data["weight"]
                    if abs(this_match) > abs(best_match):
                        best_match = this_match

            if best_match != 0:
                match_str = str(int(np.round(best_match * 100))) + "%"
                if best_match < 0:
                    match_str += _(" (opposite sense)")  # TODO
            else:
                match_str = ""
            this_q_variants.append(match_str)

            if question_text is not None and question_text != "":
                texts_for_topic_extraction.append(question_text)

        df_harmonised_text[str(idx)] = this_q_variants

    # Find the keywords describing each column and change the column headers if applicable.
    keywords = get_keywords_for_groups(list_of_lists_of_texts)
    columns = list(df_harmonised_text.columns)
    for idx, kw in enumerate(keywords):
        if kw != "":
            columns[idx + 3] = kw
    df_harmonised_text.columns = columns

    return df_harmonised, df_harmonised_text


def add_manual_edges_to_generated_graph(G: nx.Graph, manual_edges: dict):
    """
    Take the network graph which was generated automatically, and add any extra edges which the user has configured.
    :param G: The network graph.
    :param manual_edges: A dictionary of all manual edges, going from tuples of (node1, node2) to edge weight.
    """
    for edge, value in manual_edges.items():
        if edge[0] not in G or edge[1] not in G:
            continue
        if edge in G.edges:
            G.remove_edge(edge[0], edge[1])
        if value != 0:
            G.add_edge(edge[0], edge[1], weight=value, source="manual")


def get_question_dfs(df_questions: pd.DataFrame) -> tuple:
    question_dfs = []

    files = []
    for filename in df_questions.filename:
        if filename not in files:
            files.append(filename)

    for filename in files:
        this_df = df_questions[df_questions.filename == filename]
        this_df.attrs["language"] = get_clean_language_code(this_df.language.iloc[0])
        question_dfs.append(this_df)
    return files, question_dfs


def convert_similarities_into_network_graph(question_dfs: list, matches: dict, sensitivity: float,
                                            is_allow_matches_within_instrument: bool,
                                            is_allow_multiple_edges_per_node: bool) -> nx.Graph:
    # Make a network graph
    G = nx.Graph()

    for questionnaire_idx in range(len(question_dfs)):
        for row_idx in range(len(question_dfs[questionnaire_idx])):
            if question_dfs[questionnaire_idx].is_include.iloc[row_idx]:
                G.add_node((questionnaire_idx, row_idx))

    nodes_already_seen_for_document_pair = {}
    for doc1_node1_doc2_node2_tuple, match_strength in sorted(matches.items(), key=lambda kv: abs(kv[1]), reverse=True):
        if abs(match_strength) < sensitivity:
            break

        document_pair = tuple(sorted([doc1_node1_doc2_node2_tuple[0], doc1_node1_doc2_node2_tuple[2]]))

        if not is_allow_matches_within_instrument and document_pair[0] == document_pair[1]:
            continue

        n1 = (doc1_node1_doc2_node2_tuple[0], doc1_node1_doc2_node2_tuple[1])
        n2 = (doc1_node1_doc2_node2_tuple[2], doc1_node1_doc2_node2_tuple[3])

        if n1 not in G or n2 not in G:
            continue

        if document_pair not in nodes_already_seen_for_document_pair:
            nodes_already_seen_for_document_pair[document_pair] = set()
        nodes_already_seen = nodes_already_seen_for_document_pair[document_pair]

        if is_allow_multiple_edges_per_node or (n1 not in nodes_already_seen and n2 not in nodes_already_seen):
            G.add_edge(n1, n2, weight=match_strength)
            nodes_already_seen.add(n1)
            nodes_already_seen.add(n2)

    return G
