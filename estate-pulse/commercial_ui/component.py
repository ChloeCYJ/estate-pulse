from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import streamlit as st


COMPONENT_QUALIFIED_NAME = "commercial_ui.commercial_ui"
_component_renderer = None


def get_component_build_dir() -> Path:
    return Path(__file__).resolve().parent / "frontend" / "build"


def render_commercial_ui(
    *,
    page: str,
    view_model: dict[str, Any],
    key: str,
    frontend_state: dict[str, Any] | None = None,
) -> Any:
    renderer = _get_component_renderer()
    data = {
        "page": page,
        "view_model": view_model,
        "frontend_state": frontend_state or {},
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "locale": "ko-KR",
        },
    }
    return renderer(
        key=key,
        data=data,
        width="stretch",
        height="content",
        on_search_submitted_change=lambda: None,
        on_recent_analysis_selected_change=lambda: None,
        on_navigation_selected_change=lambda: None,
    )


def _get_component_renderer():
    global _component_renderer
    if _component_renderer is None:
        _component_renderer = st.components.v2.component(
            COMPONENT_QUALIFIED_NAME,
            html=" ",
            js="commercial-ui.js",
            css="commercial-ui.css",
            isolate_styles=True,
        )
    return _component_renderer
