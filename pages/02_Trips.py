# pages/03_Trips.py (or your Trips page)
import os
import pandas as pd
import streamlit as st
from datetime import datetime

from utils.left_pane import setup_left_pane
from utils.header import inject_top_header

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(page_title="Trips", page_icon="🚛", layout="wide")

# Left pane + top header
setup_left_pane()
inject_top_header("Trips Management")

# Keep content snug under header
st.markdown("""
<style>
/* Reduce padding under top header for tighter alignment */
section.main > div.block-container { padding-top: 0 !important; }
</style>
""", unsafe_allow_html=True)

# ==============================
# CONSTANTS – exact column labels you specified
# ==============================
DATE_LABEL     = "Departure Date"   # column 6
PLATE_LABEL    = "Plate Number"     # column 2
CUSTOMER_LABEL = "Customer"         # column 11
KM_LABEL       = "Fixed Km"

# ==============================
# DATA LOADER – fetch ALL rows from Supabase (paged)
# ==============================
@st.cache_data(ttl=300, show_spinner=False)
def _load_all_imports(page_size=5000, max_pages=200):
    """
    Returns (df, where_used).
    Tries:
      1) tms.imports
      2) public."tms.imports"
    Fetches ALL rows using .range() pagination.
    """
    from supabase import create_client

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_ANON_KEY", "").strip()
    if not url or not key:
        raise RuntimeError("Missing SUPABASE_URL / SUPABASE_ANON_KEY environment variables.")

    client = create_client(url, key)

    def fetch_all(schema_name, table_name):
        pg = client.postgrest.schema(schema_name)
        # Count first (minimal range)
        head = (
            pg.from_(table_name)
            .select("*", count="exact")
            .range(0, 0)
            .execute()
        )
        total = head.count or 0
        if total == 0:
            return pd.DataFrame([])

        frames, fetched, pages = [], 0, 0
        while fetched < total and pages < max_pages:
            start = fetched
            end = min(fetched + page_size - 1, total - 1)
            res = (
                pg.from_(table_name)
                .select("*")
                .range(start, end)
                .execute()
            )
            part = pd.DataFrame(res.data or [])
            frames.append(part)
            n = len(part)
            fetched += n
            pages += 1
            if n == 0:
                break

        return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame([])

    # Attempt 1: tms.imports
    try:
        df1 = fetch_all("tms", "imports")
        return df1, "tms.imports"
    except Exception:
        pass

    # Attempt 2: quoted table in public
    try:
        df2 = fetch_all("public", "tms.imports")
        return df2, 'public."tms.imports"'
    except Exception as e:
        raise RuntimeError(f"Could not read from tms.imports nor public.\"tms.imports\": {e}")

# ==============================
# Controls row
# ==============================
cols_ctrl = st.columns([1, 6])
with cols_ctrl[0]:
    if st.button("↻ Refresh", help="Reload table & analytics (cache 5 min)"):
        _load_all_imports.clear()

# ==============================
# Load data
# ==============================
try:
    df_raw, where_used = _load_all_imports()
except Exception as e:
    st.error(f"Could not load imports: {e}")
    st.stop()

# Tidy columns
df_raw.columns = [c.strip() for c in df_raw.columns]

# Drop unwanted column if present
if "import_id" in df_raw.columns:
    df_raw = df_raw.drop(columns=["import_id"])

# Resolve exact headers (case/space-insensitive)
def resolve_col(df, target_label):
    tl = target_label.strip().lower()
    for c in df.columns:
        if c.strip().lower() == tl:
            return c
    return None

DATE_COL     = resolve_col(df_raw, DATE_LABEL)
PLATE_COL    = resolve_col(df_raw, PLATE_LABEL)
CUSTOMER_COL = resolve_col(df_raw, CUSTOMER_LABEL)
KM_COL       = resolve_col(df_raw, KM_LABEL)

# Parse dates robustly
if DATE_COL:
    s = pd.to_datetime(df_raw[DATE_COL], errors="coerce")
    # If many NaT, try dayfirst=True
    if s.isna().mean() > 0.5:
        s2 = pd.to_datetime(df_raw[DATE_COL], errors="coerce", dayfirst=True)
        if s2.notna().sum() > s.notna().sum():
            s = s2
    df_raw[DATE_COL] = s

st.caption(f"Source: **{where_used}** • Rows loaded: **{len(df_raw):,}**")

st.markdown("---")

# ==============================
# Top Pane: Analytics (left) + Filters (right)
# ==============================
left, right = st.columns([2, 1], vertical_alignment="top")

# ---- Filters (right) ----
with right:
    st.markdown("### Filters")

    date_from = date_to = None
    if DATE_COL and not df_raw.empty:
        nn = df_raw.dropna(subset=[DATE_COL])
        if not nn.empty:
            min_d = nn[DATE_COL].min().date()
            max_d = nn[DATE_COL].max().date()
            c1, c2 = st.columns(2)
            with c1:
                date_from = st.date_input("From", value=min_d, min_value=min_d, max_value=max_d, key="flt_from")
            with c2:
                date_to = st.date_input("To", value=max_d, min_value=min_d, max_value=max_d, key="flt_to")
        else:
            st.caption("No valid dates found in data.")
    else:
        st.caption("No date column detected.")

    plate_choice = None
    if PLATE_COL and not df_raw.empty:
        plates = ["All"] + sorted([str(x) for x in df_raw[PLATE_COL].dropna().unique()])
        plate_choice = st.selectbox("Plate", plates, index=0, key="flt_plate")
    else:
        st.caption("No plate column detected.")

# Apply filters globally (affects analytics + table)
df = df_raw.copy()

if DATE_COL and date_from and date_to:
    try:
        df = df[(df[DATE_COL].dt.date >= date_from) & (df[DATE_COL].dt.date <= date_to)]
    except Exception:
        pass

if PLATE_COL and plate_choice and plate_choice != "All":
    df = df[df[PLATE_COL].astype(str) == str(plate_choice)]

# ---- Analytics (left) ----
with left:
    st.markdown("### Analytics")

    m1, m2 = st.columns(2)
    with m1:
        st.metric("No. of Trips", len(df))
    with m2:
        if KM_COL and KM_COL in df.columns:
            km_sum = pd.to_numeric(df[KM_COL], errors="coerce").fillna(0).sum()
            st.metric("Km Driven", f"{km_sum:,.0f} km")
        else:
            st.metric("Km Driven", "N/A")

    st.markdown("**Top 5 Customers**")
    if CUSTOMER_COL and CUSTOMER_COL in df.columns and not df.empty:
        top_cust = (
            df[CUSTOMER_COL]
            .astype(str)
            .value_counts()
            .head(5)
            .reset_index()
            .rename(columns={"index": "Customer", CUSTOMER_COL: "Trips"})
        )
        st.table(top_cust)
    else:
        st.caption("Column 'Customer' not found.")

    st.markdown("**Top 3 Trucks (by trips)**")
    if PLATE_COL and PLATE_COL in df.columns and not df.empty:
        top_trucks = (
            df[PLATE_COL]
            .astype(str)
            .value_counts()
            .head(3)
            .reset_index()
            .rename(columns={"index": "Plate Number", PLATE_COL: "Trips"})
        )
        st.table(top_trucks)
    else:
        st.caption("No plate column detected.")

st.markdown("---")

# ==============================
# Filtered Table (with 1-based Ref.)
# ==============================
st.markdown("### Trip Records (filtered)")
if df.empty:
    st.info("No rows match the selected filters.")
else:
    df_display = df.copy()

    # Ensure no existing Ref/Ref. columns conflict
    for c in ("Ref", "Ref."):
        if c in df_display.columns:
            df_display = df_display.drop(columns=[c])

    # Insert 1-based Ref. as first column
    df_display.insert(0, "Ref.", range(1, len(df_display) + 1))

    # Show table
    try:
        st.dataframe(df_display, use_container_width=True, height=500, hide_index=True)
    except TypeError:
        st.dataframe(df_display, use_container_width=True, height=500)

    # Export filtered results
    st.download_button(
        "Download filtered trips as CSV",
        data=df_display.to_csv(index=False),
        file_name=f"imports_filtered_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )
