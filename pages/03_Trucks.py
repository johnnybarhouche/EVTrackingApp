import streamlit as st
import pandas as pd
from utils.left_pane import setup_left_pane
from utils.header import inject_top_header
from utils.db import fetch_table, to_df
from streamlit.components.v1 import html as html_comp
import html as _html  # safe escaping

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Trucks",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----- Global styling / left pane -----
setup_left_pane()
inject_top_header("Trucks Management")

# -----------------------------
# Zero ALL top/inner gaps so content is flush under header
# -----------------------------
st.markdown("""
<style>
/* 1) Kill Streamlit’s first spacer under the header */
section.main > div.block-container > div:first-child {
  display: none !important;
}

/* 2) Remove top padding of the page container */
section.main > div.block-container {
  padding-top: 0 !important;
  margin-top: 0 !important;
  padding-left: 0 !important;
}

/* 3) Nuke margins/padding on all building blocks + element wrappers */
section.main [data-testid="stVerticalBlock"],
section.main [data-testid="stHorizontalBlock"],
section.main [data-testid="stElementContainer"],
section.main [data-testid="column"] {
  margin: 0 !important;
  padding: 0 !important;
  gap: 0 !important;
}

/* 4) Keep columns tight (title+button row) */
div[data-testid="column"] > div {
  margin: 0 !important;
  padding: 0 !important;
}

/* 5) Tight heading so descenders (like 'g') aren’t clipped */
.block-container h3 {
  margin: 0 !important;
  padding: 0 0 2px 0 !important;  /* tiny bottom pad avoids clipping */
  line-height: 1.25 !important;
  color: #002664 !important;
  font-size: 1.4rem !important;
  font-weight: 500 !important;
}

/* 6) Compact refresh button */
div.stButton > button {
  padding-top: 0.25rem !important;
  padding-bottom: 0.25rem !important;
  min-height: 28px !important;
}

/* 7) Remove default bottom margin Streamlit adds between elements */
section.main div.block-container p, 
section.main div.block-container div, 
section.main div.block-container table {
  margin-bottom: 0 !important;
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
# HTML table (auto-fit; no inner scrolling, no extra top margin)
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

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  html, body {{
    margin: 0;
    padding: 0;       /* <-- critical: no top margin inside iframe */
  }}
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
</head>
<body>
  <table class="dsv-table">
    <thead><tr>{thead}</tr></thead>
    <tbody>{tbody}</tbody>
  </table>
</body>
</html>
"""
    # Height sized to content; cap to avoid runaway height
    approx_height = min(120 + 36 * max(len(df), 1), 1200)
    html_comp(html, height=approx_height, scrolling=False)

# -----------------------------
# Initial load (first visit)
# -----------------------------
if "truck_master_data" not in st.session_state:
    try:
        st.session_state.truck_master_data = load_mapped_ev_trucks_df()
    except Exception as e:
        st.session_state.truck_master_data = pd.DataFrame()
        st.error(f"Could not load trucks: {e}")

# -----------------------------
# Header row: title (left) + compact refresh (right), flush under header
# -----------------------------
left, right = st.columns([12, 1])
with left:
    st.markdown('<h3>EV HD Trucks Master Data</h3>', unsafe_allow_html=True)
with right:
    if st.button("↻ Refresh", help="Refresh data", use_container_width=True):
        try:
            st.cache_data.clear()
        except Exception:
            pass
        st.session_state.truck_master_data = load_mapped_ev_trucks_df()

# -----------------------------
# Table directly after title row (no extra elements in between)
# -----------------------------
df = st.session_state.truck_master_data
if not df.empty:
    render_trucks_table_autofit(df)
else:
    st.info("No truck master data available.")
