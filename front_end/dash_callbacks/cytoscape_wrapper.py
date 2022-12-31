import json

import numpy as np

from dash_callbacks.graph_utils import get_number_of_question, get_text_of_question


def get_cyto_stylesheet():
    CYTO_STYLESHEET = [
        {
            'selector': 'node',
            'style': {
                'label': 'data(label)',
                'text-valign': 'center',
                'text-halign': 'center',
                "text-wrap": "wrap",
                'shape': 'roundrectangle',
                # 'content': 'data(label)',
                'width': 350,
                'text-max-width': 320,
                'height': 60,
                'font-family': 'PT Sans',
                'border-color': '#000000',
                'border-width': 2,
                'border-opacity': 0.5
                # 'opacity': 1,
            }
        },
        {
            'selector': '$node > node',
            'style': {
                'padding-top': '10px',
                'padding-left': '10px',
                'padding-bottom': '10px',
                'padding-right': '10px',
                'text-valign': 'top',
                'text-halign': 'center',
                'background-color': '#ddd',
                # 'opacity': 0.7,#
                'font-family': 'PT Sans',
                'font-size': '20pt'
            }
        }
    ]

    for idx, colour in enumerate(
            [u'#1f77b4', u'#ff7f0e', u'#2ca02c', u'#d62728', u'#9467bd', u'#8c564b', u'#e377c2', u'#7f7f7f',
             u'#bcbd22',
             u'#17becf'] * 2):
        CYTO_STYLESHEET.append(
            {
                'selector': '.class' + str(idx),
                'style': {
                    'background-color': colour,
                    'text-outline-width': 2,
                    'text-outline-color': colour,
                    'color': '#fff',
                    # 'opacity': 1,
                }
            }
        )
    CYTO_STYLESHEET.append(
        {
            'selector': '.unassigned',
            'style': {
                'background-opacity': 0,
                'border-opacity': 0,
            }
        }
    )

    CYTO_STYLESHEET.append(
        {
            'selector': 'edge',
            'style': {
                'curve-style': 'bezier',
                'width': 'data(myWidth)',
                'line-color': 'data(colour)',
                'label': 'data(label)',
                'line-style': 'data(linestyle)'
            }
        }
    )
    CYTO_STYLESHEET.append(
        {
            'selector': "edge[label]",
            'style': {
                "label": "data(label)",
                "text-rotation": "autorotate",
                "text-margin-x": "0px",
                "text-margin-y": "0px",
                'text-background-color': "data(matchStrengthColour)",
                'text-background-opacity': 1,
                'font-family': 'PT Sans',
                'font-size': '20pt',
                'border-color': '#000000',
                'border-width': 2,
                'border-opacity': 0.5,
            }
        },
    )
    return CYTO_STYLESHEET


def get_node_options_with_cytoscape_colour_scheme(question_dfs):
    node_options = []
    file_colours = ["🔵", "🟠", "🟢", "🔴", "🟣", "🟤", "🔴", "⚪", "🟢", "🔵"] * 2
    for file_idx, question_df in enumerate(question_dfs):
        for idx in range(len(question_df)):
            label = file_colours[file_idx]
            if question_df.question_no.iloc[idx] is not None:
                label += " " + str(question_df.question_no.iloc[idx]) + "."
            label += " " + question_df.question.iloc[idx]
            option = {"value": str((file_idx, idx)),
                      "label": label}
            node_options.append(option)
    return node_options


def get_edge_colour(sign):
    if sign > 0:
        return "#008800"
    return "#ff0000"


def get_edge_match_strength_colour(edge_strength):
    if abs(edge_strength) > 0.9:
        return "#22ff22"
    if abs(edge_strength) > 0.5:
        return "#ffaa66"
    return "#ff5555"


def get_edge_style(edge_source: str) -> str:
    if edge_source == "manual":
        return "solid"
    return "dotted"


def get_percent_label_string(weight: float, edge_source: str) -> str:
    if edge_source == "manual":
        if weight < 0:
            return "manual negative"
        else:
            return "manual positive"
    value = str(int(np.round(100 * weight))) + "%"
    if "-" not in value:
        value = "+" + value
    return value


def make_cytoscape_graph(files, question_dfs, G, df_harmonised, _):
    # This part is building the graph in a format to pass to Cyto

    is_found_edges_for_file = set()
    for node, attr in G.nodes.items():
        if len(G.edges(node)) > 0:
            is_found_edges_for_file.add(node[0])

    is_graph_has_edges_from_each_file = len(is_found_edges_for_file) == len(files)

    def get_node_parent(short):
        if not is_graph_has_edges_from_each_file:  # if no edges in graph
            return files[short[0]]
        if len(G.edges(short)) > 0:
            return files[short[0]]
        return None

    nodes = [
        {
            'data': {'id': str(node_id_tuple),
                     'label': get_number_of_question(question_dfs, node_id_tuple) + get_text_of_question(question_dfs,
                                                                                                         node_id_tuple),
                     'parent': get_node_parent(node_id_tuple)},
            'classes': f"class{node_id_tuple[0]}"
        }
        for node_id_tuple, attr in G.nodes.items()
    ]
    # Add the files as separate parent nodes.
    for file_idx, file in enumerate(files):
        if question_dfs[file_idx].is_include.any():
            nodes.append({'data': {'id': file, 'text': file, 'label': file}})

    edges = []
    for source, target in G.edges:
        networkx_edge_data = G.get_edge_data(source, target)
        weight = networkx_edge_data['weight']
        edge_source = networkx_edge_data.get("source")
        edge = {'data': {'source': str(source), 'target': str(target),
                         'myWidth': float(15 * abs(weight)),
                         'label': get_percent_label_string(weight, edge_source),
                         'polarity': float(np.sign(weight)),
                         'colour': get_edge_colour(np.sign(weight)),
                         'matchStrengthColour': get_edge_match_strength_colour(weight),
                         'linestyle': get_edge_style(edge_source),
                         }}
        edges.append(edge)

    elements = nodes + edges

    print("elements", json.dumps(elements))

    # Make the Cytoscape style

    columns_and_rows = {}
    height_of_column = [0] * len(df_harmonised)
    for i in range(len(df_harmonised)):
        for j in range(len(df_harmonised.columns)):
            cell = df_harmonised[df_harmonised.columns[j]].iloc[i]

            if cell is None:
                continue

            # Cells are aligned similarly to in the export Excel, but to save space we squash them together in columns.
            x = i
            y = j
            if len(G.edges(cell)) == 0:
                y = height_of_column[x] + 1
            height_of_column[x] = max([height_of_column[x], y])
            columns_and_rows[cell] = [x, y]

    # Rearrange the cells so that they fit on the screen.
    downshift = {}
    for j in range(100):
        height_of_column = [0] * max([5, len(df_harmonised)])
        for x, y in columns_and_rows.values():
            if y > height_of_column[x]:
                height_of_column[x] = y

        max_height = max(height_of_column)
        min_height = min(height_of_column)

        if max_height - min_height > 2:
            longest_column = np.argmax(height_of_column)
            shortest_column = np.argmin(height_of_column)

            lowest_cell = None
            for cell, (x, y) in columns_and_rows.items():
                if lowest_cell is None or y > columns_and_rows[lowest_cell][1]:
                    lowest_cell = cell

            # Don't shift nodes which have edges
            if len(G.edges(lowest_cell)) > 0:
                break

            columns_and_rows[lowest_cell] = [shortest_column, min_height + 1]
            downshift[lowest_cell] = 1

            # Disconnect from parents
            for e in elements:
                if "id" in e["data"] and e["data"]["id"] == str(lowest_cell):
                    e["data"]["parent"] = None

    is_paginated_unassigned_nodes = False
    for cell_id, (x, y) in columns_and_rows.items():
        if x >= len(df_harmonised):
            print("Node in extra column", cell_id, x, y)
            for e in elements:
                if "id" in e["data"] and e["data"]["id"] == str(cell_id):
                    e["data"]["parent"] = "unassigned"
                    is_paginated_unassigned_nodes = True

    if is_paginated_unassigned_nodes:
        elements.append(
            {'data': {'id': "unassigned", 'text': _("Unmatched questions"), 'label': _("Unmatched questions")},
             'classes': "unassigned"})

    pos = dict([(cell, (x * 450, y * 100 + downshift.get(cell, 0) * 50)) for cell, (x, y) in columns_and_rows.items()])

    cytoscape_layout = {
        'name': "preset",
        'animate': True,
        'positions': {
            str(node_id): {'x': pos[node_id][0], 'y': pos[node_id][1]}
            for node_id, attr in G.nodes.items()
        },
    }

    return elements, cytoscape_layout
