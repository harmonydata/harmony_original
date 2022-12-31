from dash import Output, Input, State


def add_clientside_callbacks(dash_app):
    # Hide side bar when click tab.
    dash_app.clientside_callback(
        """
        function(result) {
            const triggered = dash_clientside.callback_context.triggered.map(t => t.prop_id);
            if (triggered=="btn_show_side_bar.n_clicks") {
                document.getElementsByClassName("main")[0].style.animation = "animate_main_backwards 1s linear 1 forwards";
                document.getElementsByClassName("side_bar")[0].style.animation = "animate_side_bar_backwards 1s linear 1 forwards";
                return {"position": "absolute", "left": "0px", "top": "0px", "display":"none"};
            } else {
            document.getElementsByClassName("main")[0].style.animation = "animate_main 1s linear 1 forwards";
                document.getElementsByClassName("side_bar")[0].style.animation = "animate_side_bar 1s linear 1 forwards";
                return {"position": "absolute", "left": "0px", "top": "0px"};
            }
            
        }
        """,
        Output("btn_show_side_bar", "style"),
        [Input("btn_show_side_bar", "n_clicks"),
         Input("btn_hide_side_bar", "n_clicks")],
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


    dash_app.clientside_callback(
            """
            function(n, is_open) {
                if (n > 0) {
                    var s = {"display":"none"};
                    if (is_open["display"] == "none") {
                        s["display"] = "inline-block";
                    }
                    return s;
                }
            }
            """,
            Output("collapse", "style"),
            [Input("collapse-button", "n_clicks"),
            State("collapse", "style")],
            prevent_initial_call=True,
        )



    dash_app.clientside_callback(
            """
            function(n) {
                return [n.includes("zoom"), n.includes("pan")];
            }
            """,
            [Output("cytoscape-update-layout", "userPanningEnabled"),
             Output("cytoscape-update-layout", "userZoomingEnabled")],
            [Input("zoompan", "value")],
            prevent_initial_call=True,
        )

    dash_app.clientside_callback(
        """
        function(n) {
            const triggered = dash_clientside.callback_context.triggered.map(t => t.prop_id);
            if (triggered=="btn_go_to_2.n_clicks") {
                return "tab_check_the_matches";
            } else {
                return "tab_export_excel";
            }
        }
        """,
        Output("tabs", "value"),
        [Input("btn_go_to_2", "n_clicks"),
         Input("btn_go_to_3", "n_clicks")],
        prevent_initial_call=True,
    )
