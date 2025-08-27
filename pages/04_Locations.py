# pages/04_Locations.py

import os
import io
import re
from datetime import datetime

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from utils.left_pane import setup_left_pane
from utils.header import inject_top_header

# Optional import guard for supabase
try:
    from supabase import create_client
except Exception:
    create_client = None

# -------------------------------------------
# Page config & styling
# -------------------------------------------
st.set_page_config(page_title="Locations", page_icon="📍", layout="wide")

setup_left_pane()
inject_top_header("Trips Management")

PRIMARY = "#002664"
st.markdown(
    f"""
    <style>
      h1, h2, h3 {{ color: {PRIMARY} !important; }}
      .stButton > button {{ background-color: {PRIMARY}; color: white; }}
      [data-testid="metric-container"] {{ background: white; border: 1px solid #e0e0e0; border-radius: 8px; }}
      section.main > div.block-container {{ padding-top: 0.5rem !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("📍 Location Management")
st.subheader("Manage Pickup and Delivery Locations")

# -------------------------------------------
# Supabase helpers (Replit Secrets)
# -------------------------------------------
@st.cache_resource(show_spinner=False)
def get_supabase():
    if create_client is None:
        raise RuntimeError("supabase-py is not installed. Add it to your environment.")
    url = os.environ.get("SUPABASE_URL") or os.environ.get("SUPABASE_PROJECT_URL")
    key = (
        os.environ.get("SUPABASE_KEY")
        or os.environ.get("SUPABASE_ANON_KEY")
        or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    )
    if not url or not key:
        st.error(
            "Supabase credentials not found.\n\n"
            "In Replit, add Secrets:\n"
            "- SUPABASE_URL\n- SUPABASE_KEY"
        )
        st.stop()
    return create_client(url, key)

LOC_TABLE = "locations"  # ensure this matches your Supabase table name

def load_locations_df():
    sb = get_supabase()
    res = sb.table(LOC_TABLE).select("*").order("location_name").execute()
    df = pd.DataFrame(res.data or [])
    # normalize expected columns
    for col in ["id", "location_name", "lat", "lng", "added_by", "remark"]:
        if col not in df.columns:
            df[col] = None
    # keep consistent ordering
    return df[["id", "location_name", "lat", "lng", "added_by", "remark"]].copy()

def upsert_locations(rows):
    if not rows:
        return
    sb = get_supabase()
    sb.table(LOC_TABLE).upsert(rows, on_conflict="location_name").execute()

def insert_locations(rows):
    if not rows:
        return
    sb = get_supabase()
    sb.table(LOC_TABLE).insert(rows).execute()

def update_location_by_id(row_id, updates: dict):
    if not updates:
        return
    sb = get_supabase()
    sb.table(LOC_TABLE).update(updates).eq("id", row_id).execute()

# -------------------------------------------
# Session state
# -------------------------------------------
if "locations_df" not in st.session_state:
    st.session_state.locations_df = pd.DataFrame()
if "original_df" not in st.session_state:
    st.session_state.original_df = pd.DataFrame()
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# -------------------------------------------
# Utilities
# -------------------------------------------
LAT_RE = re.compile(r"^-?([1-8]?\d(\.\d+)?|90(\.0+)?)$")
LNG_RE = re.compile(r"^-?((1[0-7]\d)|(\d{1,2}))(\.\d+)?$|^-?180(\.0+)?$")  # -180..180

def is_valid_lat(v) -> bool:
    try:
        s = str(v).strip()
        float(s)
        return bool(LAT_RE.match(s))
    except Exception:
        return False

def is_valid_lng(v) -> bool:
    try:
        s = str(v).strip()
        float(s)
        return bool(LNG_RE.match(s))
    except Exception:
        return False

def now_ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def ensure_loaded():
    if st.session_state.locations_df.empty:
        st.session_state.locations_df = load_locations_df()
        st.session_state.original_df = st.session_state.locations_df.copy()

# -------------------------------------------
# Header row: user name + refresh
# -------------------------------------------
left, right = st.columns([6, 1])
with left:
    st.text_input(
        "Your name (used for 'Added via website by ...' and change remarks)",
        key="user_name",
        placeholder="e.g., Johnny",
    )
with right:
    if st.button("↻ Refresh", use_container_width=True):
        st.cache_data.clear()
        st.session_state.locations_df = load_locations_df()
        st.session_state.original_df = st.session_state.locations_df.copy()
        st.success("Locations refreshed.")

# -------------------------------------------
# Load data & build search options
# -------------------------------------------
ensure_loaded()

if st.session_state.locations_df.empty:
    st.info("No locations found in the database yet. Add locations below or import a file.")
    location_names = []
else:
    location_names = (
        st.session_state.locations_df["location_name"]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )
    location_names.sort()

# Typeahead select (only valid names)
selected_loc = st.selectbox(
    "Search locations",
    options=["All locations"] + location_names,
    index=0,
    help="Start typing to search; only valid locations are selectable.",
)

# Build filtered view for both table and map
df_view = st.session_state.locations_df.copy()
if selected_loc != "All locations":
    df_view = df_view[df_view["location_name"] == selected_loc]

# -------------------------------------------
# Editable table
# -------------------------------------------
if not st.session_state.locations_df.empty:
    st.markdown("#### Current Locations")
    edited = st.data_editor(
        df_view,
        key="locations_editor",
        use_container_width=True,
        column_config={
            "id": st.column_config.Column("ID", disabled=True, help="Database ID"),
            "location_name": st.column_config.TextColumn("Location Name", required=True),
            "lat": st.column_config.NumberColumn("Lat", step=0.000001, format="%.6f"),
            "lng": st.column_config.NumberColumn("Lng", step=0.000001, format="%.6f"),
            "added_by": st.column_config.TextColumn("Added by", disabled=True),
            "remark": st.column_config.TextColumn("Remark", disabled=True),
        },
        num_rows="dynamic",
        hide_index=True,
    )

    if st.button("💾 Save Edits"):
        user = (st.session_state.user_name or "Unknown").strip()
        # Align edited rows with original by ID
        orig = st.session_state.original_df.set_index("id", drop=False)
        curr = edited.set_index("id", drop=False)

        changed_count, errors = 0, 0

        for rid, row in curr.iterrows():
            # New inline row without an ID -> treat as upsert by name
            if pd.isna(rid) or (rid not in orig.index):
                loc = (row.get("location_name") or "").strip()
                if not loc:
                    continue
                lat = row.get("lat", None)
                lng = row.get("lng", None)
                if not (is_valid_lat(lat) and is_valid_lng(lng)):
                    st.error(f"Invalid lat/lng for new row '{loc}'.")
                    errors += 1
                    continue
                payload = {
                    "location_name": loc,
                    "lat": float(lat),
                    "lng": float(lng),
                    "added_by": f"Added via website by {user}",
                    "remark": f"Added via website by {user} on {now_ts()}",
                }
                try:
                    upsert_locations([payload])
                    changed_count += 1
                except Exception as e:
                    st.error(f"Insert failed for '{loc}': {e}")
                    errors += 1
                continue

            # Existing row: compare with original
            o = orig.loc[rid]
            updates, remark_bits = {}, []

            new_name = (row.get("location_name") or "").strip()
            old_name = (o.get("location_name") or "").strip()
            if new_name != old_name:
                if not new_name:
                    st.error(f"Location name cannot be empty (ID {rid}).")
                    errors += 1
                else:
                    updates["location_name"] = new_name
                    remark_bits.append(f"Name changed by {user}")

            new_lat = row.get("lat", None)
            new_lng = row.get("lng", None)

            if pd.notna(new_lat) and not is_valid_lat(new_lat):
                st.error(f"Invalid latitude for '{new_name or old_name}'.")
                errors += 1
            if pd.notna(new_lng) and not is_valid_lng(new_lng):
                st.error(f"Invalid longitude for '{new_name or old_name}'.")
                errors += 1

            if pd.notna(new_lat) and (pd.isna(o.get("lat")) or float(new_lat) != float(o.get("lat"))):
                updates["lat"] = float(new_lat)
                remark_bits.append(f"Lat changed by {user}")

            if pd.notna(new_lng) and (pd.isna(o.get("lng")) or float(new_lng) != float(o.get("lng"))):
                updates["lng"] = float(new_lng)
                remark_bits.append(f"Lng changed by {user}")

            if updates:
                existing = (o.get("remark") or "").strip()
                stamp = f"{'; '.join(remark_bits)} on {now_ts()}"
                updates["remark"] = f"{existing + ' | ' if existing else ''}{stamp}"

                try:
                    update_location_by_id(int(rid), updates)
                    changed_count += 1
                except Exception as e:
                    st.error(f"Update failed (ID {rid}): {e}")
                    errors += 1

        # Reload after save
        st.session_state.locations_df = load_locations_df()
        st.session_state.original_df = st.session_state.locations_df.copy()

        if changed_count and not errors:
            st.success(f"Saved {changed_count} change(s).")
        elif changed_count and errors:
            st.warning(f"Saved {changed_count} change(s) with {errors} error(s).")
        elif not changed_count and not errors:
            st.info("No changes detected.")

# -------------------------------------------
# Add new location (single)
# -------------------------------------------
st.markdown("### Add New Location")
with st.form("add_location_form", clear_on_submit=True):
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        new_name = st.text_input("Location Name", placeholder="e.g., Warehouse A")
    with c2:
        new_lat = st.text_input("Lat", placeholder="e.g., 24.453884")
    with c3:
        new_lng = st.text_input("Lng", placeholder="e.g., 54.377344")

    submitted = st.form_submit_button("➕ Add Location")
    if submitted:
        user = (st.session_state.user_name or "Unknown").strip()
        if not new_name.strip():
            st.error("Please provide a location name.")
        elif not (is_valid_lat(new_lat) and is_valid_lng(new_lng)):
            st.error("Invalid coordinates. Check Lat (-90..90) and Lng (-180..180).")
        else:
            payload = {
                "location_name": new_name.strip(),
                "lat": float(new_lat),
                "lng": float(new_lng),
                "added_by": f"Added via website by {user}",
                "remark": f"Added via website by {user} on {now_ts()}",
            }
            try:
                upsert_locations([payload])  # upsert by location_name
                st.success(f"Location '{new_name}' saved.")
                st.session_state.locations_df = load_locations_df()
                st.session_state.original_df = st.session_state.locations_df.copy()
            except Exception as e:
                st.error(f"Failed to save location: {e}")

# -------------------------------------------
# Import (CSV or Excel): location_name, lat, lng
# -------------------------------------------
st.markdown("### Import Locations (CSV/Excel)")
with st.expander("Upload file (columns: location_name, lat, lng)"):
    file = st.file_uploader("Choose file", type=["csv", "xlsx", "xls"])
    if file is not None:
        try:
            if file.name.lower().endswith(".csv"):
                imp = pd.read_csv(file)
            else:
                imp = pd.read_excel(file)

            required = ["location_name", "lat", "lng"]
            missing = [c for c in required if c not in imp.columns]
            if missing:
                st.error(f"Missing required columns: {', '.join(missing)}")
            else:
                user = (st.session_state.user_name or "Unknown").strip()
                rows, errs = [], []

                for i, r in imp.iterrows():
                    name = str(r["location_name"]).strip() if pd.notna(r["location_name"]) else ""
                    lat = r["lat"]
                    lng = r["lng"]
                    if not name:
                        errs.append(f"Row {i+2}: empty location_name")
                        continue
                    if not (is_valid_lat(lat) and is_valid_lng(lng)):
                        errs.append(f"Row {i+2}: invalid lat/lng for '{name}'")
                        continue
                    rows.append(
                        {
                            "location_name": name,
                            "lat": float(lat),
                            "lng": float(lng),
                            "added_by": f"Added via website by {user}",
                            "remark": f"Added via website by {user} on {now_ts()}",
                        }
                    )

                if errs:
                    for e in errs:
                        st.error(e)

                if rows:
                    st.write("Preview:")
                    st.dataframe(pd.DataFrame(rows), use_container_width=True)

                    if st.button("📤 Import to Database"):
                        try:
                            upsert_locations(rows)
                            st.success(f"Imported {len(rows)} location(s).")
                            st.session_state.locations_df = load_locations_df()
                            st.session_state.original_df = st.session_state.locations_df.copy()
                        except Exception as e:
                            st.error(f"Import failed: {e}")

        except Exception as e:
            st.error(f"Error reading file: {e}")

# -------------------------------------------
# Export helpers
# -------------------------------------------
if not st.session_state.locations_df.empty:
    st.markdown("### Export Locations")
    c1, c2 = st.columns(2)
    with c1:
        csv = st.session_state.locations_df.to_csv(index=False)
        st.download_button(
            "Download CSV",
            csv,
            file_name=f"locations_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
        )
    with c2:
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            st.session_state.locations_df.to_excel(writer, index=False, sheet_name="Locations")
        st.download_button(
            "Download Excel",
            buf.getvalue(),
            file_name=f"locations_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# -------------------------------------------
# Map (filtered by typeahead)
# -------------------------------------------
st.markdown("### Location Map")
map_df = df_view.dropna(subset=["lat", "lng"])
if map_df.empty:
    st.info("No matching locations (or no valid coordinates) for the current selection.")
else:
    coords = map_df[["lat", "lng"]].astype(float).values.tolist()
    center_lat = map_df["lat"].astype(float).mean()
    center_lng = map_df["lng"].astype(float).mean()
    zoom = 12 if len(coords) == 1 else 8

    fmap = folium.Map(location=[center_lat, center_lng], zoom_start=zoom)

    for _, r in map_df.iterrows():
        try:
            folium.Marker(
                [float(r["lat"]), float(r["lng"])],
                popup=r["location_name"],
                tooltip=r["location_name"],
            ).add_to(fmap)
        except Exception:
            continue

    if len(coords) > 1:
        fmap.fit_bounds(coords)

    st_folium(fmap, width=900, height=520)
