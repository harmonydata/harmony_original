import json

from dash import Output, Input

with open("localisation/translations.json", "r", encoding="utf-8") as f:
    LANGUAGE_STRINGS = f.read()

parsed_language_strings = json.loads(LANGUAGE_STRINGS)
outputs = []
for parse_language_tuple in parsed_language_strings:
    outputs.append(Output(parse_language_tuple[0], parse_language_tuple[1]))


def add_gettext_callbacks(dash_app):
    dash_app.clientside_callback("""function(language) {
var texts = """ + LANGUAGE_STRINGS + """;
    if (language == "pt") {
        return texts.map(function(x) { return x[3]; } );
    } else {
        return texts.map(function(x) { return x[2]; } );
    }
}
""", outputs,
                                 [Input("select_language", "value")],
                                 )


    dash_app.clientside_callback("""function(x) {
        return x;
    }
    """, Output("filter_topic_threshold", "marks"),
                                     Input("my-slider", "marks"),
                                     )
