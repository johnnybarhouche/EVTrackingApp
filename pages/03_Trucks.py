import streamlit as st
import pandas as pd
from utils.left_pane import setup_left_pane
from utils.header import inject_top_header
from utils.db import fetch_table, to_df
from streamlit.components.v1 import html as html_comp
import html as _html  # for safe escaping

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Trucks", page_icon="🚚", layout="wide", initial_sidebar_state="expanded")

# ----- Global styling / left pane -----
setup_left_pane()
inject_top_header("Trucks Management")

# Remove all empty sections and gaps above content
st.markdown("""
<style>
/* Completely remove default padding and margins */
section.main > div.block-container { 
  padding-top: 0 !important; 
  padding-left: 0 !important; 
  margin-top: 0 !important;
}

/* Kill ALL vertical blocks that might create spacing */
section.main > div.block-container > div[data-testid="stVerticalBlock"] {
  margin-top: 0 !important;
  padding-top: 0 !important;
  min-height: 0 !important;
}

/* Hide empty blocks completely */
section.main > div.block-container > div[data-testid="stVerticalBlock"]:empty,
section.main > div.block-container > div[data-testid="stVerticalBlock"] > div:only-child:empty {
  display: none !important;
}

/* Remove margins from all elements that could create gaps */
section.main div.block-container h1,
section.main div.block-container h2,
section.main div.block-container h3,
section.main div.block-container div,
section.main div.block-container p { 
  margin-top: 0 !important; 
  padding-top: 0 !important;
}

/* Ensure columns don't add spacing */
div[data-testid="column"] {
  margin-top: 0 !important;
  padding-top: 0 !important;
}

/* Force negative pull-up if needed */
section.main > div.block-container { 
  transform: translateY(-8px); 
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Data loader (mapped & trimmed)
# -----------------------------
def load_mapped_ev_trucks_df() -> pd.DataFrame:
    """
    Fetch only the required columns from ev.trucks and rename for display.
    """
    records = fetch_table(
        "ev.trucks",
        select="truck_id, plate_number, make, model, battery_kwh"
    )
    df = to_df(records)
    if df.empty:
        return df

    display_map = {
        "truck_id": "Truck ID",
        "plate_number": "Plate Number",
        "make": "Make",
        "model": "Model",
        "battery_kwh": "Battery, kWh",
    }
    df = df.rename(columns=display_map)
    df = df[list(display_map.values())]  # keep only mapped columns
    return df

# -----------------------------
# HTML table (auto-fit; no inner scrolling)
# -----------------------------
def render_trucks_table_autofit(df: pd.DataFrame):
    base_cols = ["Truck ID", "Plate Number", "Make", "Model", "Battery, kWh"]
    df = df[base_cols].copy().reset_index(drop=True)

    # Add Ref. column (1..n) at the start
    df.insert(0, "Ref.", range(1, len(df) + 1))
    cols = ["Ref."] + base_cols

    thead = "".join(f"<th>{_html.escape(c)}</th>" for c in cols)
    tbody = "\n".join(
        "<tr>" + "".join(f"<td>{_html.escape(str(v))}</td>" for v in row) + "</tr>"
        for row in df[cols].values.tolist()
    )

    html = f"""
    <style>
      .dsv-table {{
        width: 100%;
        border-collapse: collapse;
        border-spacing: 0;
        table-layout: auto;                 /* auto-fit by content */
        font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      }}
      .dsv-table th, .dsv-table td {{
        border: 1px solid #E5E7EB;
        padding: 8px 12px;
        text-align: center;
        vertical-align: middle;
      }}
      .dsv-table thead th {{
        background: #BCDBEC;               /* header bg */
        color: #002664;                    /* header font */
        font-weight: 700;                  /* bold */
        white-space: nowrap;
      }}
      .dsv-table tbody td {{
        background: #FFFFFF;               /* body cells white */
        white-space: normal;               /* allow wrapping for auto-height */
        word-break: break-word;
        line-height: 1.3;
      }}
    </style>
    <table class="dsv-table">
      <thead><tr>{thead}</tr></thead>
      <tbody>{tbody}</tbody>
    </table>
    """

    # Height sized to content; cap to avoid runaway height
    approx_height = min(120 + 36 * max(len(df), 1), 1200)
    html_comp(html, height=approx_height, scrolling=False)

# -----------------------------
# Always show table + compact Refresh
# -----------------------------
# Initial load (first visit)
if "truck_master_data" not in st.session_state:
    try:
        st.session_state.truck_master_data = load_mapped_ev_trucks_df()
    except Exception as e:
        st.session_state.truck_master_data = pd.DataFrame()
        st.error(f"Could not load trucks: {e}")



# Title + compact refresh (sits directly under header, aligned left)
left, right = st.columns([10, 2], gap="small")
with left:
    st.markdown('<h3 style="margin:0;">EV HD Trucks Master Data</h3>', unsafe_allow_html=True)
with right:
    if st.button("↻", key="refresh", help="Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.session_state.truck_master_data = load_mapped_ev_trucks_df()



# Render table
df = st.session_state.truck_master_data
if not df.empty:
    render_trucks_table_autofit(df)
else:
    st.info("No truck master data available.")