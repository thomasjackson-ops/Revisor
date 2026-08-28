"""Tema visual de la aplicación: paleta OpenBeauchef (azul/rojo), estilo minimalista tech."""

from __future__ import annotations

import base64
import textwrap
from pathlib import Path

import streamlit as st

LOGO_PATH = Path(__file__).parent.parent / "recursos" / "OB.png"

# Paleta extraída del logo OpenBeauchef
BLUE_DARK = "#073763"
BLUE = "#0B4F8C"
BLUE_LIGHT = "#E8F1FA"
BLUE_SOFT = "#F4F8FC"
RED_ACCENT = "#E2231A"
TEXT_DARK = "#152B42"
TEXT_MUTED = "#5B7186"


def get_logo_base64() -> str:
    if not LOGO_PATH.exists():
        return ""
    return base64.b64encode(LOGO_PATH.read_bytes()).decode()


def inject_theme() -> None:
    """Inyecta CSS global con la paleta de OpenBeauchef y tipografía moderna."""
    css = f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet">
        <style>
        html, body, [class*="css"] {{
            font-family: 'Manrope', 'Segoe UI', sans-serif;
        }}

        .stApp {{
            background: linear-gradient(180deg, {BLUE_SOFT} 0%, #FFFFFF 55%);
            color: {TEXT_DARK};
        }}

        /* Fuerza tema claro aunque el SO/navegador esté en modo oscuro */
        [data-testid="stHeader"] {{
            background: #FFFFFF !important;
        }}
        [data-testid="stAppViewContainer"], [data-testid="stMain"], .main {{
            color: {TEXT_DARK} !important;
        }}
        p, span, label, li, div {{
            color: inherit;
        }}
        h1, h2, h3, h4, h5, h6, .stMarkdown, [data-testid="stMarkdownContainer"] {{
            color: {TEXT_DARK} !important;
        }}

        /* Inputs, textareas y selects en el contenido principal */
        [data-testid="stAppViewContainer"] input,
        [data-testid="stAppViewContainer"] textarea,
        [data-testid="stAppViewContainer"] [data-baseweb="select"] > div,
        [data-testid="stAppViewContainer"] [data-baseweb="base-input"] {{
            background-color: #FFFFFF !important;
            color: {TEXT_DARK} !important;
            border-radius: 8px !important;
            border: 1px solid #C9D9E8 !important;
        }}
        [data-testid="stAppViewContainer"] [data-baseweb="select"] * {{
            color: {TEXT_DARK} !important;
        }}
        [data-testid="stAppViewContainer"] textarea::placeholder,
        [data-testid="stAppViewContainer"] input::placeholder {{
            color: {TEXT_MUTED} !important;
            opacity: 1;
        }}

        /* Menú desplegable (opciones del selectbox) */
        [data-baseweb="popover"] [data-baseweb="menu"] {{
            background-color: #FFFFFF !important;
        }}
        [data-baseweb="popover"] li {{
            color: {TEXT_DARK} !important;
        }}

        /* --- Sidebar --- */
        [data-testid="stSidebar"] {{
            background: linear-gradient(195deg, {BLUE_DARK} 0%, {BLUE} 100%);
        }}
        [data-testid="stSidebar"] * {{
            color: #F2F7FC !important;
        }}
        [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {{
            color: #FFFFFF !important;
            font-weight: 800 !important;
        }}
        [data-testid="stSidebar"] hr {{
            border-color: rgba(255,255,255,0.18);
        }}
        [data-testid="stSidebar"] input, [data-testid="stSidebar"] textarea,
        [data-testid="stSidebar"] [data-baseweb="select"] > div {{
            background-color: rgba(255,255,255,0.96) !important;
            color: {TEXT_DARK} !important;
            border-radius: 8px !important;
        }}
        [data-testid="stSidebar"] [data-baseweb="select"] * {{
            color: {TEXT_DARK} !important;
        }}

        /* --- Header / topbar card --- */
        .ob-topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1.5rem;
            background: #FFFFFF;
            border-radius: 18px;
            padding: 1.1rem 1.6rem;
            box-shadow: 0 4px 24px rgba(11, 79, 140, 0.10);
            border: 1px solid {BLUE_LIGHT};
            margin-bottom: 1.25rem;
        }}
        .ob-topbar-text h1 {{
            margin: 0;
            font-size: 1.55rem;
            font-weight: 800;
            color: {TEXT_DARK};
            letter-spacing: -0.01em;
        }}
        .ob-topbar-text p {{
            margin: 0.15rem 0 0 0;
            color: {TEXT_MUTED};
            font-size: 0.92rem;
        }}
        .ob-topbar img {{
            height: 42px;
            object-fit: contain;
        }}
        .ob-accent-dot {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: {RED_ACCENT};
            margin-right: 6px;
        }}

        /* --- Headings --- */
        h1, h2, h3 {{
            color: {TEXT_DARK};
        }}

        /* --- Tabs --- */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 6px;
            background: {BLUE_LIGHT};
            padding: 6px;
            border-radius: 12px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 9px;
            padding: 8px 18px;
            color: {BLUE};
            font-weight: 600;
        }}
        .stTabs [aria-selected="true"] {{
            background: {BLUE} !important;
            color: #FFFFFF !important;
            box-shadow: 0 2px 10px rgba(11,79,140,0.25);
        }}

        /* --- Buttons --- */
        .stButton > button {{
            background: {BLUE};
            color: #FFFFFF;
            border: none;
            border-radius: 10px;
            font-weight: 700;
            padding: 0.55rem 1.1rem;
            transition: all 0.15s ease-in-out;
            box-shadow: 0 2px 8px rgba(11,79,140,0.18);
        }}
        .stButton > button:hover {{
            background: {BLUE_DARK};
            box-shadow: 0 4px 14px rgba(11,79,140,0.28);
            transform: translateY(-1px);
        }}
        .stButton > button:disabled {{
            background: #C9D6E3;
            color: #7C8CA0;
            box-shadow: none;
        }}

        .stDownloadButton > button {{
            background: #FFFFFF;
            color: {BLUE};
            border: 1.5px solid {BLUE};
            border-radius: 10px;
            font-weight: 700;
            transition: all 0.15s ease-in-out;
        }}
        .stDownloadButton > button:hover {{
            background: {BLUE_LIGHT};
            border-color: {BLUE_DARK};
            color: {BLUE_DARK};
        }}

        /* --- Expander (filas de estudiante) --- */
        [data-testid="stExpander"] {{
            border: 1px solid {BLUE_LIGHT};
            border-left: 4px solid {BLUE};
            border-radius: 12px;
            background: #FFFFFF;
            box-shadow: 0 2px 10px rgba(11,79,140,0.06);
            margin-bottom: 0.6rem;
        }}
        [data-testid="stExpander"] summary {{
            font-weight: 700;
            color: {TEXT_DARK};
        }}

        /* --- Metrics --- */
        [data-testid="stMetric"] {{
            background: {BLUE_LIGHT};
            border-radius: 12px;
            padding: 0.8rem 1rem;
            border: 1px solid rgba(11,79,140,0.10);
        }}
        [data-testid="stMetricValue"] {{
            color: {BLUE_DARK} !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: {TEXT_MUTED} !important;
        }}

        [data-testid="stCaptionContainer"] {{
            color: {TEXT_MUTED} !important;
        }}

        /* --- Alerts --- */
        [data-testid="stAlert"] {{
            border-radius: 12px;
        }}

        /* --- Dataframe --- */
        [data-testid="stDataFrame"] {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid {BLUE_LIGHT};
        }}

        /* --- Generic containers used as cards via st.container(key=...) --- */
        .st-key-rubric_card, .st-key-course_card, .st-key-batch_card, .st-key-zip_card {{
            background: #FFFFFF;
            border-radius: 16px;
            padding: 1.4rem 1.6rem;
            border: 1px solid {BLUE_LIGHT};
            box-shadow: 0 2px 14px rgba(11,79,140,0.06);
            margin-bottom: 1rem;
        }}

        [data-testid="stFileUploaderDropzone"] {{
            border-radius: 12px;
            border: 1.5px dashed {BLUE};
            background: {BLUE_LIGHT};
        }}
        </style>
        """
    st.html(textwrap.dedent(css))


def render_header(title: str, subtitle: str) -> None:
    """Header con título/subtítulo a la izquierda y el logo OpenBeauchef a la derecha."""
    logo_b64 = get_logo_base64()
    logo_html = (
        f'<img src="data:image/png;base64,{logo_b64}" alt="OpenBeauchef" />' if logo_b64 else ""
    )
    header_html = f"""
        <div class="ob-topbar">
            <div class="ob-topbar-text">
                <h1><span class="ob-accent-dot"></span>{title}</h1>
                <p>{subtitle}</p>
            </div>
            {logo_html}
        </div>
        """
    st.html(textwrap.dedent(header_html))
