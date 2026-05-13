"""Detail drawer callbacks: populate drawer content from selected task."""

from __future__ import annotations

from dash import Input, Output, State, callback, no_update
from dash.exceptions import PreventUpdate

from stride.ui.components.detail import build_detail_content


def register_callbacks(app):
    @app.callback(
        Output("detail-header-meta", "children"),
        Output("detail-title", "children"),
        Output("detail-description", "children"),
        Output("detail-fields", "children"),
        Output("detail-history", "children"),
        Output("detail-counters", "children"),
        Output("detail-drawer", "opened", allow_duplicate=True),
        Input("store-selected", "data"),
        Input("btn-close-drawer", "n_clicks"),
        State("store-tasks", "data"),
        prevent_initial_call=True,
    )
    def populate_detail(selected_id, close_clicks, tasks):
        from dash import ctx
        triggered = ctx.triggered_id

        if triggered == "btn-close-drawer":
            return no_update, no_update, no_update, no_update, no_update, no_update, False

        if not selected_id or not tasks:
            raise PreventUpdate

        # Find the task
        task = next((t for t in tasks if t.get("id") == selected_id), None)
        if task is None:
            raise PreventUpdate

        header_meta, title_el, desc_el, fields_el, history_el, counters_el = (
            build_detail_content(task)
        )

        return (
            header_meta,
            title_el,
            desc_el,
            fields_el,
            history_el,
            counters_el,
            no_update,  # don't change opened state here — card_cb handles opening
        )
