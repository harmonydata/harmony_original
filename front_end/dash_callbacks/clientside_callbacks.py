from dash import Output, Input


def add_clientside_callbacks(dash_app):
    # Hide side bar when click tab.
    dash_app.clientside_callback(
        """
        function(result) {
            if (result == "tab_upload_your_data") {
                document.getElementsByClassName("main")[0].style.animation = "animate_main_backwards 1s linear 1 forwards";
                document.getElementsByClassName("side_bar")[0].style.animation = "animate_side_bar_backwards 1s linear 1 forwards";
            } else {
            document.getElementsByClassName("main")[0].style.animation = "animate_main 1s linear 1 forwards";
                document.getElementsByClassName("side_bar")[0].style.animation = "animate_side_bar 1s linear 1 forwards";

            }
            
        }
        """,
        Output("dummy2", "data"),
        Input("tabs", "value"),
        prevent_initial_call=True,
    )

    # Show/hide the tooltips depending on button presses and cookie
    dash_app.clientside_callback(
        """
        function(btn_hide, btn_show, is_visited_before) {
            if (btn_hide == undefined) {
                btn_hide = 0;
            }
            if (btn_show == undefined) {
                btn_show = 0;
            }
            if ((btn_hide + btn_show + is_visited_before) % 2 == 1) {
                return {"display":"none"};
            }
            return {};
        }
        """,
        Output("twtooltip0", "style"),
        [Input("twtooltip0", "n_clicks"),
         Input("btn_show_tip0", "n_clicks"),
         Input("is_visited_before", "data")],
        prevent_initial_call=True,
    )

    # Show/hide the tooltips depending on button presses and cookie
    dash_app.clientside_callback(
        """
        function(btn_hide, btn_show, is_visited_before) {
            if (btn_hide == undefined) {
                btn_hide = 0;
            }
            if (btn_show == undefined) {
                btn_show = 0;
            }
            if ((btn_hide + btn_show + is_visited_before) % 2 == 1) {
                return {"display":"none"};
            }
            return {};
        }
        """,
        Output("twtooltip1", "style"),
        [Input("twtooltip1", "n_clicks"),
         Input("btn_show_tip1", "n_clicks"),
         Input("is_visited_before", "data")],
        prevent_initial_call=True,
    )
