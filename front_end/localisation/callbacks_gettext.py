import json

from dash import Output, Input

with open("localisation/translations.js", "r", encoding="utf-8") as f:
    LANGUAGE_STRINGS = f.read()

parsed_language_strings = json.loads(LANGUAGE_STRINGS)
outputs = []
for k, v, e, p in parsed_language_strings:
    outputs.append(Output(k, v))


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
