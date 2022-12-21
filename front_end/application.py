import gettext, os


FOLDER_OF_THIS_FILE = os.path.dirname(os.path.abspath(__file__))
print (os.path.join(FOLDER_OF_THIS_FILE, 'locale'))
pt_lang = gettext.translation('body', localedir=os.path.join(FOLDER_OF_THIS_FILE, 'locale'), languages=['pt'])


import dash

from localisation.callbacks_gettext import add_gettext_callbacks
# from dash_callbacks.callbacks_view_1 import add_view_1_callbacks
# from dash_callbacks.callbacks_view_2 import add_view_2_callbacks
from dash_callbacks.clientside_callbacks import add_clientside_callbacks
from dash_layout.body import get_body



# ------------------------------------------------------ APP ------------------------------------------------------

dash_app = dash.Dash(__name__, meta_tags=[{"name": "viewport", "content": "width=device-width"},
                                          {"name": "description",
                                           "content": "Analyse your mental health questionnaires and harmonise them using Natural Language Processing."}],
                     external_scripts=["https://www.googletagmanager.com/gtag/js?id=G-1QPLVX52QG"],
                     )
dash_app.title = "Harmony"

server = dash_app.server

# Create app layout
dash_app.layout = get_body(dash_app)

# ------------------------------------------------------ Callbacks ------------------------------------------------------

add_gettext_callbacks(dash_app)
#
# add_view_1_callbacks(dash_app)
#
# add_view_2_callbacks(dash_app)

add_clientside_callbacks(dash_app)

if __name__ == "__main__":
    port = os.environ.get('dash_port', 8050)
    debug = os.environ.get('dash_debug') == "True"
    dash_app.run_server(debug=debug, host="0.0.0.0", port=port)
