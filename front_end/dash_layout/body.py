import bz2
import os
import pickle as pkl

import dash_core_components as dcc
import dash_cytoscape as cyto
import dash_html_components as html
from dash import dash_table

file_to_text = {}
dataset_selector_style = None
if True:
    try:
        file_name = os.path.join(os.path.dirname(__file__), '../hard_coded_questionnaires/questionnaires.pkl.bz2')
        with bz2.open(file_name, "rb") as f:
            file_to_text = pkl.load(f)
    except:
        print("Could not find any preprocessed questionnaires")
        print("The document selector menu will be hidden.")
        dataset_selector_style = {"display": "none"}

# The options to display in the dropdown for each y and x_i.
dataset_options = [
    {"label": dataset, "value": dataset}
    for dataset in sorted(file_to_text)
]

rows = [
    dcc.Location(id='url', refresh=False),
    dcc.Store("is_visited_before"),
    dcc.Store("blank_output"),
    dcc.Store("blank_output_2"),
    dcc.Store("blank_output_3"),
    dcc.Store("dummy1"),
    dcc.Store("dummy2"),
    dcc.Store("manual_edges"),
    dcc.Store("document_content"),
    dcc.Store("similaritystore"),
    dcc.Tabs(
        [dcc.Tab([

            html.Div(
                [
                    html.Div([

                        html.Div([
                            html.P(className="control_label", id="choose_existing_questionnaires",
                                   style=dataset_selector_style),
                            dcc.Dropdown(
                                id="dataset",
                                options=dataset_options,
                                multi=True,
                                value=None,
                                className="dcc_control",
                                style=dataset_selector_style
                            ),
                            html.P(style=dataset_selector_style, id="or"),
                            html.P([html.Span("Upload your documents ", id="upload_your_documents"),
                                    html.Button(id="btn_show_tip0")], className="control_label"),

                            dcc.Upload(id='upload-data',
                                       children=html.Div([
                                           html.Span('Drag and Drop PDFs or Excels', id="drag_drop"), html.Br(),
                                           html.Span(' or ', id="or2"), html.Br(),
                                           html.A('Select Files from your Computer', id="select_files")
                                       ]),
                                       style={
                                           # 'width': '100%',
                                           'height': '120px',
                                           'lineHeight': '40px',
                                           'borderWidth': '1px',
                                           'borderStyle': 'dashed',
                                           'borderRadius': '5px',
                                           'textAlign': 'center',
                                           'margin': '10px'
                                       },

                                       # Allow multiple files to be uploaded
                                       multiple=True,
                                       accept="application/pdf,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                       ),

                            html.Div([dcc.Markdown(id="tip0"),
                                      html.Button(id="twtooltipbtnexit0",
                                                  className="tooltipbutton")],
                                     className="twbox sb2 twtooltip",
                                     id="twtooltip0"
                                     ),

                        ], style={'float': 'left', 'width': '50%', 'margin-left': '10px', 'margin-right': '10px'}),

                        html.Div([
                            html.P(className="control_label", id="files_selected"),
                            html.Span(

                                [dcc.Loading([dash_table.DataTable(
                                    id="file_table",
                                    editable=True,
                                    row_deletable=True,
                                    page_size=200,
                                    style_cell={"font-size": "10pt", "font-family": "PT Sans", "textAlign": "left",
                                                "background-color": "white"}

                                )]), ],
                                className="file_selector"
                            ),
                        ], style={'float': 'left', 'width': '50%'})

                    ], className="box", style={"display": "flex"}),

                    html.Div(
                        [

                            html.P(className="control_label", id="these_are_questions"),

                            html.Div([
                                html.P(id="click_to_filter", className="control_label",
                                       style={'float': 'left'}),
                                dcc.Dropdown(id="filter_questions", options=[], value=None, multi=False,
                                             style={'float': 'left', 'width': '50%', "margin-left": "20px"})],
                                style={"display": "flex", "width": "100%"}),
                            html.Button("+", id="add_row"),

                            dcc.Loading([
                                dash_table.DataTable(
                                    id="excerpt_table",
                                    editable=True,
                                    row_deletable=True,
                                    page_size=200,
                                    sort_action='native',
                                    filter_action='native',
                                    export_format="xlsx",
                                    row_selectable=True,
                                    filter_options={"case":"insensitive"},
                                    style_cell={"font-size": "10pt", "font-family": "PT Sans", "textAlign": "left",
                                                "background-color": "white"})])

                        ], className="box"),

                ],

            ),

        ], id="upload_your_data", value="tab_upload_your_data", className="box tab",
            selected_className='tab-active'),

            dcc.Tab([
                html.Div([
                    html.Div(
                        [
                            html.Button(id="btn_calculate_match"),
                            html.Button(id="btn_save_graph"),
                            html.Button(id="btn_show_tip1"),

                            # html.P(
                            #     "Below you can see the questions where Harmony found a match."),

                            html.P(
                                id="adjust_sensitivity"),
                            dcc.Slider(0, 1, 0.1, value=0.3,
                                       id='my-slider',

                                       ),
                            html.P(
                                id="filter_by_cat"),
                            dcc.Dropdown(
                                id='dropdown-categories',
                                value=None,
                                clearable=True,
                                multi=True,
                            ),
                        ],
                        className="box", style={"display": "inline-block", "width": "45%", "vertical-align": "top"}),
                    html.Div(
                        [
                            html.P(
                                id="click_to_add_remove"),

                            dcc.Dropdown(
                                id='dropdown-selected',
                                value=None,
                                clearable=True,
                                multi=True,
                            ),
                            dcc.Dropdown(
                                id='dropdown-edge',
                                value=None,
                                options=[{"value": 1, "label": "positive"}, {"value": -1, "label": "negative"},
                                         {"value": 0, "label": "no connection"}],
                            ),
                            html.Button(id="btn_update_edge",
                                        ),
                            html.Button(id="btn_clear_edge",
                                        ),

                        ],
                        className="box", style={"display": "inline-block", "width": "45%", "vertical-align": "top"}),

                ], id="box_graph_controls", style={"display": "none"}  # TODO

                ),

                html.Div([
                    dcc.Loading([
                        html.Span([
                            html.H3(
                                id="please_upload_message"),
                            html.H3(
                                id="please_wait_message", style={"display": "none"})],
                            id="all_loading_messages"
                        )
                    ]),

                    html.Div([dcc.Markdown(id="tooltip1_markdown"),
                              html.Button(id="twtooltipbtnexit",
                                          className="tooltipbutton")],
                             className="twbox sb2 twtooltip",
                             id="twtooltip1"
                             ),
                    cyto.Cytoscape(
                        zoom=500,
                        id='cytoscape-update-layout',
                        layout={'name': 'preset'},
                        # boxSelectionEnabled=False,
                        # autounselectify=True,
                        style={'width': '100%', 'height': '1000px'},
                        # elements=elements

                        # stylesheet=cyto_stylesheet,
                    )

                ],
                    className="box"
                ),

            ], id="check_the_matches", value="tab_check_the_matches", className="box"),

            dcc.Tab([

                html.Div(
                    [
                        # html.Button("Generate table", id="btn_create_table"),
                        # html.P(
                        #     "Here are your results."),
                        dash_table.DataTable(
                            id="results_table",
                            editable=True,
                            row_deletable=False,
                            export_format="xlsx", page_size=20,

                        ),
                    ],
                    className="box"
                ),

            ], id="export_excel", value="tab_export_excel", className="box"),

        ], id="tabs", value="tab_upload_your_data"

    ),

    # html.Div([
    #
    #     html.Div([
    #
    #        html.Div([ html.Span("➊", style={"font-size":"15pt"}),  """ Upload your data.""", html.Span(["done"], style={"right":"0px", "float":"right"}, className="donebutton")], className="box", style={"height":"55px"}),
    #
    #
    #
    #
    #     ],
    #              style={ 'padding-top':'15px', 'padding-bottom':'15px', 'width':'33%','float':'left'}
    #              ),
    #     html.Div([
    #
    #         html.Div([html.Span("➋", style={"font-size": "15pt"}), """ Check the matches.""", html.Span(["continue ⤏"], style={"right":"0px", "float":"right"}, className="continuebutton")], className="box", style={"height":"55px"}),
    #
    #         html.Div([], className="box", style={"margin-right":"-500px"})
    #     ],
    #              style={'padding-top': '15px', 'padding-bottom': '15px', 'width': '33%','float':'left'}
    #              )
    # ,
    #     html.Div([
    #
    #         html.Div([html.Span("➌", style={"font-size": "15pt"}), """ Export or save the results."""], className="box", style={"height":"55px"}),
    #
    #     ],
    #              style={ 'padding-top': '15px', 'padding-bottom': '15px', 'width': '33%','float':'left'}
    #              )
    #
    #
    # ], style={'margin': '10px', 'padding-top': '15px', 'padding-bottom': '15px', 'display':'flex'}),

]

rows.append(

    html.Div(
        [

            html.Span(id="built_by"),
            html.A(["Thomas Wood"], href="https://freelancedatascientist.net", target="freelance"),
            html.Span(id="at"),
            html.A(["Fast Data Science"], href="https://fastdatascience.com", target="fds"),
            ". ",
            html.A(href="https://github.com/harmonydata/harmony",
                   target="github", id="github"),
            "."
        ],
        className="attribution"
    ),

)

rows.append(html.Div([], id="log_tika", style={"opacity": "0.1"}))


def get_body(dash_app):
    return html.Div([

        html.Div([
            html.Img(src=dash_app.get_asset_url('logo-no-background.png'),
                     # style={'position': 'relative', 'width': '180%', 'left': '-83px', 'top': '-20px'}
                     style={"width": "100%", "margin-top": "20px"}
                     ),
            # html.H1(children='Harmony'),
            dcc.Dropdown(
                options=[{"label": "🇬🇧🇺🇸 English", "value": "en"}, {"label": "🇧🇷🇵🇹 Português", "value": "pt"}],
                id="select_language", value="en", multi=False),
            dcc.Markdown(style={'color': 'white'}, className="introtext", id="introtext"),
            html.Img(id="harmony_graphic",
                     # style={'position': 'relative', 'width': '180%', 'left': '-83px', 'top': '-20px'}
                     style={"width": "100%"}
                     ),
        ], className='side_bar', id="side_bar"),

        html.Div(
            html.Div(rows, className='main', id="main"),
        ),
    ])
