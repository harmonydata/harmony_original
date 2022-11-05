from dash import Input, Output


def add_gettext_callbacks(dash_app):
    @dash_app.callback(output=[Output("introtext", "children"),
                               Output("choose_existing_questionnaires", "children"),
                               Output("or", "children"),
                               Output("upload_your_documents", "children"),
                               Output("btn_show_tip0", "children"),
                               Output("drag_drop", "children"),
                               Output("or2", "children"),
                               Output("select_files", "children"),
                               Output("tip0", "children"),
                               Output("twtooltipbtnexit0", "children"),
                               Output("files_selected", "children"),
                               Output("these_are_questions", "children"),
                               Output("click_to_filter", "children"),
                               Output("upload_your_data", "label"),
                               Output("check_the_matches", "label"),
                               Output("export_excel", "label"),
                               Output("btn_calculate_match", "children"),
                               Output("btn_save_graph", "children"),
                               Output("btn_show_tip1", "children"),
                               Output("adjust_sensitivity", "children"),
                               Output("my-slider", "marks"),
                               Output("click_to_add_remove", "children"),
                               Output("btn_update_edge", "children"),
                               Output("btn_clear_edge", "children"),
                               Output("tooltip1_markdown", "children"),
                               Output("twtooltipbtnexit", "children"),
                               Output("built_by", "children"),
                               Output("at", "children"),
                               Output("github", "children"),
                               Output("please_upload_message", "children"),
                               Output("please_wait_message", "children"),
                               Output("filter_by_cat", "children"),
                               Output("harmony_graphic", "src"),
                               Output("dropdown-edge", "options")
                               ],
                       inputs=[Input("select_language", "value")
                               ]
                       )
    def find_if_tooltip_cookie_present(language):
        if language == "pt":
            from application import pt_lang
            _ = pt_lang.gettext
        else:
            _ = lambda x: x

        return [
            _("""Harmony is a tool designed for retrospective harmonisation of questionnaire data.

If you want to compare data from different surveys, such as GAD-7 and PHQ-9, Harmony can identify which questions match.

Drag and drop your spreadsheets and PDFs of mental health questionnaires into the tool.

The AI will harmonise your data.

You can export the result to Excel or as an image, and share with colleagues.

Read more at [harmonydata.org](https://harmonydata.org).

You can also read our [privacy policy](https://harmonydata.org/privacy-policy/)."""),
            _("Choose existing questionnaires"),
            _("or"),
            _("Upload your documents "),
            _("How should I format the documents?"),
            _('Drag and Drop PDFs or Excels'),
            _("or"),
            _('Select Files from your Computer'),
            _("""Harmony can read questionnaires in PDF or Excel format, although Excels may give better results.

If you're using Excel, each file should be an Excel spreadsheet with a question on each row. You can put multiple questionnaires in a single Excel in different sheets.

If you're uploading a PDF file, for best results the questions should be formatted with question numbers, question text and a list of options on each line, e.g.

```
1. Feeling nervous: Rarely, Sometimes, Often, Always
```

This version of the Harmony tool supports English and Portuguese documents."""),
            _("Hide tip"),
            _("Files selected"),
            _("These are the questions that Harmony found in your documents."),
            _("Click to filter by a particular file:"),
            _("➊ Upload your data"),
            _("➋ Check the matches"),
            _("➌ Export the matches to Excel"),
            _("Click to re-calculate all the matching questions"),
            _("Click to save this graph to your computer"),
            _("Show/hide tip"),
            _("Adjust the sensitivity of the matches. If this is high, only questions with exactly the same text are considered identical. If you don't see any matches, try reducing the sensitivity."),
            {0: _("0% (show everything)"),
             0.2: _("20% (approximate matches)"),
             0.5: "50%",
             0.8: _("80% (close matches)"),
             1: _("100% (exact matches)")},
            _("You can click on a question or a connection in the graph to add or remove individual links:"),
            _("Update value of connection"),
            _("Clear all manual connections"),
            _(
                """## Using the graph

You can use the scroll wheel on your mouse to zoom in or out. You can also click and drag the graph left or right to pan across it.

The percent scores show how close the AI thought two texts matched. Exact matches score 100%. Negative values mean that the texts match but have opposite meanings, e.g. "I feel nervous" vs "I feel relaxed".

## How does Harmony work?

*The technical details*

The AI converts the text of each question into a vector in 1600 dimensions using a neural network called GPT-2. This technique is called a *document embedding*.

The distance between any two questions is measured according to the cosine similarity metric between the two vectors. Two questions which are similar in meaning, even if worded differently or in different languages, will have a high degree of similarity between their vector representations. Questions which are very different tend to be far apart in the vector space.
"""),
            _("Hide tip"),
            _("AI tool built by "),
            _(" at "),
            _("View source code on Github"),
            _("Please upload some questionnaires under 'Upload your data'."),
            _("Please wait. The graph is being calculated."),
            _("Filter questions by category:"),
            dash_app.get_asset_url(_('harmony_flowchart_en.png')),
            [{"value": 1, "label": _("positive")}, {"value": -1, "label": _("negative")},
            {"value": 0, "label": _("no connection")}]
        ]
