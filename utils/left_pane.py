# utils/left_pane.py
import os
import base64
from pathlib import Path
from typing import Optional
import streamlit as st


# ------------------------- helpers -------------------------

def _best_path(user_path: str) -> Optional[Path]:
    """Try several locations to resolve an asset path."""
    here = Path(__file__).resolve().parent
    candidates = [
        Path(user_path),
        Path(os.getcwd()) / user_path,
        here / user_path,
        here / ".." / user_path,
        here.parent / "assets" / "dsv_logo.png",   # common case
        Path("assets/dsv_logo.png"),
        Path("/app/assets/dsv_logo.png"),          # some hosts
    ]
    for p in candidates:
        try:
            if p.exists() and p.is_file():
                return p.resolve()
        except Exception:
            pass
    return None


@st.cache_data
def _b64_from_path(p: str) -> str:
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _b64_logo(user_path: str) -> str:
    p = _best_path(user_path)
    if not p:
        return ""
    try:
        return _b64_from_path(str(p))
    except Exception:
        return ""


# ------------------------- public API -------------------------

def setup_left_pane(
    *,
    # Sidebar (left pane) styling — DSV defaults
    sidebar_width_px: int = 210,
    sidebar_font_size_px: int = 23,
    link_padding_v_px: int = 2,          # vertical padding inside each link
    link_gap_v_px: int = 1,              # vertical gap between links
    sidebar_top_padding_px: int = 120,   # moves links below the logo
    # Sidebar logo (in the blue strip) — base64 background
    sidebar_logo_path: str = "assets/dsv_logo.png",
    sidebar_logo_width_px: int = 270,
    sidebar_logo_height_px: int = 90,
    sidebar_logo_left_px: int = 10,
    sidebar_logo_top_px: int = 10,
    # Fonts
    body_font_import: bool = True,   # import Roboto for body
    foundry_font_path: Optional[str] = "assets/Foundry%20Sterling/bold%20headline.otf",
    # Misc
    hide_keyboard_label: bool = True,
) -> None:
    """
    Inject CSS for the left pane (sidebar) and global theme.
    Call once at the top of every page.
    """
    # fonts
    roboto_css = (
        "@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700&display=swap');"
        if body_font_import else ""
    )
    foundry_css = ""
    if foundry_font_path:
        foundry_css = f"""
        @font-face {{
          font-family: 'Foundry Sterling';
          src: url('{foundry_font_path}') format('opentype');
          font-weight: 700;
          font-style: normal;
          font-display: swap;
        }}
        """

    # sidebar logo base64 (matches your older working approach)
    logo_b64 = _b64_logo(sidebar_logo_path)

    # optional hide keyboard label
    keyboard_hide_css = ""
    if hide_keyboard_label:
        keyboard_hide_css = """
        section[data-testid="stSidebar"] [data-testid="stSidebarContent"] > *:first-child { display: none !important; }
        section[data-testid="stSidebar"] [title*="keyboard" i],
        section[data-testid="stSidebar"] [aria-label*="keyboard" i] { display: none !important; }
        """

    st.markdown(f"""
<style>
/* ===== Fonts ===== */
{roboto_css}
{foundry_css}

/* Keep a slim top header so hamburger (sidebar toggle) stays visible */
header[data-testid="stHeader"] {{
  height: 2.5rem !important;
  background: transparent !important;
  box-shadow: none !important;
  border: 0 !important;
}}
header[data-testid="stHeader"] * {{ background: transparent !important; }}

/* App body */
.stApp {{
  background-color: #f8f9fa;
  font-family: {'Foundry Sterling' if foundry_font_path else 'Roboto'}, sans-serif;
}}
.main .block-container {{
  padding-top: 0rem;  /* header spacing handled by render_header */
  padding-left: 2rem;
  padding-right: 2rem;
  background-color: #f8f9fa;
}}

/* ===== Sidebar (left pane) ===== */
section[data-testid="stSidebar"] {{
  background-color: #002664 !important;
  border-right: 1px solid #001a4d !important;

  width: {sidebar_width_px}px !important;
  min-width: {sidebar_width_px}px !important;
  max-width: {sidebar_width_px}px !important;

  padding-top: {sidebar_top_padding_px}px !important;  /* pushes links below logo */

  position: relative;
  visibility: visible !important;
  transform: translateX(0) !important;
  opacity: 1 !important;
  z-index: 100 !important;
}}
section[data-testid="stSidebar"] > div {{ background-color: #002664 !important; }}

/* Inject the logo at the very top of the sidebar (like your old working version) */
section[data-testid="stSidebar"]::before {{
  content: "";
  position: absolute;
  top: {sidebar_logo_top_px}px;
  left: {sidebar_logo_left_px}px;
  width: {sidebar_logo_width_px}px;
  height: {sidebar_logo_height_px}px;
  background-repeat: no-repeat;
  background-size: contain;
  {'background-image: url("data:image/png;base64,' + logo_b64 + '");' if logo_b64 else ''}
  pointer-events: none;
}}

/* Sidebar text */
section[data-testid="stSidebar"] * {{
  color: #ffffff !important;
  text-align: left !important;
  font-family: {'Foundry Sterling' if foundry_font_path else 'Roboto'}, sans-serif !important;
  font-weight: 700 !important;
  font-size: {sidebar_font_size_px}px !important;
  letter-spacing: 0.2px;
  box-shadow: none !important;
  background: transparent !important;
}}

/* Sidebar links spacing + states */
section[data-testid="stSidebar"] a {{
  padding: {link_padding_v_px}px 12px !important;
  margin: {link_gap_v_px}px 0 !important;
  text-decoration: none !important;
  display: block;
  border-radius: 4px;
  transition: background-color 0.2s ease;
  background: transparent !important;
}}
section[data-testid="stSidebar"] a:hover {{
  background-color: rgba(255,255,255,0.12) !important;
  border-radius: 6px !important;
}}
section[data-testid="stSidebar"] .css-1rs6os a {{
  background-color: rgba(255,255,255,0.20) !important;
  border-radius: 6px !important;
  color: #ffffff !important;
}}

/* Hide stray "Keyboard shortcuts" label */
{keyboard_hide_css}

/* ===== Global header row (logo + title) — optional logo ===== */
#global-header {{
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 0 12px 0;  /* space under header */
}}
#global-header .global-page-title {{
  font-family: {'Foundry Sterling' if foundry_font_path else 'Roboto'}, sans-serif;
  font-weight: 700;
  line-height: 1.2;
  margin: 0;
  color: #002664;
}}

/* Tables */
.stDataFrame thead tr th,
.stDataFrame thead th,
thead tr th {{
  background-color: #002664 !important;
  color: white !important;
  font-weight: 600 !important;
  border: none !important;
  padding: 12px !important;
}}
.stDataFrame table {{
  border: 1px solid #ddd;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}}
.stDataFrame tbody tr:nth-child(even) {{ background-color: #f8f9fa; }}
.stDataFrame tbody tr:hover {{ background-color: #e3f2fd; }}

/* Metric cards */
[data-testid="metric-container"] {{
  background: white;
  border: 1px solid #e0e0e0;
  padding: 1.5rem;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  transition: box-shadow 0.3s ease;
}}
[data-testid="metric-container"]:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}

/* Buttons */
.stButton > button {{
  background-color: #002664;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 0.75rem 1.5rem;
  font-weight: 500;
  font-size: 14px;
  transition: all 0.3s ease;
}}
.stButton > button:hover {{
  background-color: #001a4d;
  color: white;
  box-shadow: 0 2px 8px rgba(0, 38, 100, 0.3);
}}

/* Headings */
h1 {{ color: #002664 !important; font-weight: 600 !important; font-size: 2.5rem !important; margin-bottom: 1rem !important; }}
h2 {{ color: #002664 !important; font-weight: 500 !important; font-size: 1.8rem !important; margin-top: 2rem !important; margin-bottom: 1rem !important; }}
h3 {{ color: #002664 !important; font-weight: 500 !important; font-size: 1.4rem !important; margin-top: 1.5rem !important; margin-bottom: 0.75rem !important; }}

/* Misc */
.streamlit-expanderHeader {{ background-color: #e8e8e8; border-radius: 6px; font-weight: 500; }}
.stAlert {{ border-radius: 6px; border-left: 4px solid #002664; }}
.stForm {{ background: white; padding: 1.5rem; border-radius: 8px; border: 1px solid #e0e0e0; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div > div {{ border: 1px solid #d0d0d0; border-radius: 4px; padding: 0.5rem; }}
.js-plotly-plot {{ border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
.stFileUploader {{ background: white; border: 2px dashed #002664; border-radius: 8px; padding: 2rem; text-align: center; }}
.stDownloadButton > button {{ background-color: #002664; color: white; border: none; border-radius: 6px; padding: 0.75rem 1.5rem; font-weight: 500; }}
.stDownloadButton > button:hover {{ background-color: #001a4d; }}
</style>
""",
        unsafe_allow_html=True,
    )


def render_header(
    title: str,
    *,
    # Optional header logo (off by default to avoid duplicate with sidebar logo)
    show_header_logo: bool = False,
    header_logo_path: str = "assets/dsv_logo.png",
    header_logo_height_px: int = 60,
    # Title options
    top_offset_px: int = 10,
    title_size_px: int = 36,
    title_color: str = "#002664",
) -> None:
    """
    Render a consistent header row with (optional) logo + page title aligned.
    Use after setup_left_pane().
    """
    logo_html = ""
    if show_header_logo:
        b64 = _b64_logo(header_logo_path)
        if b64:
            logo_html = (
                f'<img src="data:image/png;base64,{b64}" '
                f'style="height:{header_logo_height_px}px;width:auto;" alt="DSV" />'
            )
        else:
            logo_html = (
                '<div style="background:#fff;color:#002664;padding:.25rem .6rem;'
                'border-radius:4px;font-weight:700;">DSV</div>'
            )

    st.markdown(
        f"""
        <div id="global-header" style="margin-top:{top_offset_px}px;">
          {logo_html}
          <div class="global-page-title" style="font-size:{title_size_px}px; color:{title_color};">
            {title}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
