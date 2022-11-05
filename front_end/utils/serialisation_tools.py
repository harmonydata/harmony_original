import pandas as pd
import re

def deserialise_manual_edges(manual_edges_serialisable: dict):
    if manual_edges_serialisable is None:
        manual_edges_serialisable = {}
    manual_edges = {}
    for serialised_key, edge_value in manual_edges_serialisable.items():
        node_id_parts = [int(node_id_partial) for node_id_partial in serialised_key.split(",")]
        nodes = [(node_id_parts[0], node_id_parts[1]), (node_id_parts[2], node_id_parts[3])]
        node_1, node_2 = list(sorted(nodes))
        manual_edges[(node_1, node_2)] = float(edge_value)
    return manual_edges


def serialise_manual_edges(manual_edges: dict):
    if manual_edges is None:
        manual_edges = {}
    manual_edges_serialisable = {}
    for tuple_key, edge_value in manual_edges.items():
        sorted_tuple_key = list(sorted(tuple_key))
        node_1, node_2 = sorted_tuple_key
        serialised_key = ",".join([str(x) for x in (node_1[0], node_1[1], node_2[0], node_2[1])])
        manual_edges_serialisable[serialised_key] = edge_value
    return manual_edges_serialisable


def deserialise_questions_dataframe(columns, data):
    df_questions = pd.DataFrame()
    for col in columns:
        col_name = col['id']
        column_data = []
        for r in data:
            cell_data = r[col['id']]
            column_data.append(cell_data)
        df_questions[col_name] = column_data
    return df_questions


def serialise_dataframe(df: pd.DataFrame, is_natural_language=False, _=None):
    if is_natural_language:
        if _:
            preprocessing_function = lambda x: _(re.sub("_", " ", x).title())
        else:
            preprocessing_function = lambda x: re.sub("_", " ", x).title()
    else:
        if _:
            preprocessing_function = _
        else:
            preprocessing_function = lambda x: x

    serialised_columns = [{"name": preprocessing_function(i), "id": i, "hideable": True} for i in df.columns]
    serialised_data = df.to_dict('records')
    return serialised_columns, serialised_data
