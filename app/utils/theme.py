from pathlib import Path

import streamlit as st
import plotly.io as pio
import plotly.graph_objects as go

# CSS file lives at app/assets/style.css, this file lives at app/utils/theme.py
CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "style.css"

# Blue-tone colorway used across all charts for consistency
CHART_COLORWAY = [
    "#38bdf8",  # cyan
    "#2f6fed",  # blue
    "#7dd3fc",  # light cyan
    "#93c5fd",  # light blue
    "#0ea5e9",  # sky
    "#1d4ed8",  # deep blue
    "#a5f3fc",  # pale cyan
    "#60a5fa",  # mid blue
]


def _register_plotly_theme():
    """Defines a 'tourinsight' Plotly template with transparent backgrounds
    and blue-toned styling, then makes it the default for every chart —
    so px.bar / px.line calls anywhere in the app pick it up automatically,
    no need to touch individual chart code."""

    template = go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#9aa8c2", size=13),
            title=dict(font=dict(family="Sora, sans-serif", color="#eef2f8", size=18)),
            colorway=CHART_COLORWAY,
            xaxis=dict(
                gridcolor="rgba(255,255,255,0.06)",
                zerolinecolor="rgba(255,255,255,0.08)",
                linecolor="#1e2b42",
                tickfont=dict(color="#9aa8c2"),
                title=dict(font=dict(color="#9aa8c2")),
            ),
            yaxis=dict(
                gridcolor="rgba(255,255,255,0.06)",
                zerolinecolor="rgba(255,255,255,0.08)",
                linecolor="#1e2b42",
                tickfont=dict(color="#9aa8c2"),
                title=dict(font=dict(color="#9aa8c2")),
            ),
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                font=dict(color="#9aa8c2"),
            ),
            hoverlabel=dict(
                bgcolor="#101a2c",
                bordercolor="#2f6fed",
                font=dict(family="Inter, sans-serif", color="#eef2f8"),
            ),
            margin=dict(l=40, r=20, t=60, b=40),
        )
    )

    pio.templates["tourinsight"] = template
    pio.templates.default = "tourinsight"


def style_folium_map(m):
    """Injects CSS into a folium.Map's own HTML so its popups, tooltips,
    and marker clusters match the dark blue theme. Folium maps render
    inside their own iframe via streamlit_folium, so the page-level
    style.css can't reach them — this reaches in directly.

    Usage: call right after creating the map, before adding markers.
        m = folium.Map(...)
        style_folium_map(m)
    """
    import folium  # local import so pages without folium don't need it installed

    css = """
    <style>
    .leaflet-popup-content-wrapper {
        background: #101a2c;
        color: #eef2f8;
        border: 1px solid #2f6fed;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(47, 111, 237, 0.35);
        font-family: 'Inter', sans-serif;
    }
    .leaflet-popup-content {
        margin: 12px 14px;
        line-height: 1.5;
    }
    .leaflet-popup-content b {
        color: #38bdf8;
        font-family: 'Sora', sans-serif;
    }
    .leaflet-popup-tip {
        background: #101a2c;
        box-shadow: none;
    }
    a.leaflet-popup-close-button {
        color: #9aa8c2 !important;
    }
    a.leaflet-popup-close-button:hover {
        color: #38bdf8 !important;
    }

    .leaflet-tooltip {
        background: #101a2c;
        color: #eef2f8;
        border: 1px solid #1e2b42;
        font-family: 'Inter', sans-serif;
        border-radius: 6px;
    }
    .leaflet-tooltip-top:before {
        border-top-color: #101a2c;
    }

    /* Marker cluster bubbles, recolored to the blue palette */
    .marker-cluster-small {
        background-color: rgba(56, 189, 248, 0.35);
    }
    .marker-cluster-small div {
        background-color: rgba(56, 189, 248, 0.6);
        color: #060911;
        font-weight: 600;
    }
    .marker-cluster-medium {
        background-color: rgba(47, 111, 237, 0.35);
    }
    .marker-cluster-medium div {
        background-color: rgba(47, 111, 237, 0.65);
        color: #eef2f8;
        font-weight: 600;
    }
    .marker-cluster-large {
        background-color: rgba(29, 78, 216, 0.4);
    }
    .marker-cluster-large div {
        background-color: rgba(29, 78, 216, 0.75);
        color: #eef2f8;
        font-weight: 600;
    }
    </style>
    """
    m.get_root().html.add_child(folium.Element(css))
    return m


def apply_theme():
    """Call once at the top of every page, right after st.set_page_config()."""

    # Inject CSS
    if CSS_PATH.exists():
        css = CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    else:
        st.warning(f"Theme stylesheet not found at {CSS_PATH}")

    # Apply transparent blue-toned template to all Plotly charts app-wide
    _register_plotly_theme()