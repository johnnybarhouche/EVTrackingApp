import streamlit as st
import pandas as pd
from datetime import datetime
from utils.left_pane import setup_left_pane
from utils.header import inject_top_header

# ---------- Page config ----------
st.set_page_config(page_title="Data & Import", page_icon="📊", layout="wide")

# ---------- Global styling / left pane ----------
setup_left_pane()
inject_top_header("Data & Import")  # <-- This is your only page title

# ---------- Fix top spacing so content sits just under header ----------
st.markdown(
    """
    <style>
      /* Pull the main container up to sit right below the real header bar */
      div.block-container { padding-top: 0.6rem !important; }
      /* Tighten vertical rhythm for a cleaner, aligned look */
      .stTabs [data-baseweb="tab-list"] { gap: 0.25rem; }
      .stTabs [data-baseweb="tab"] { padding: 0.4rem 0.8rem; }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------- Robust session state (prevents first-load crashes) ----------
def _ensure_state():
    ss = st.session_state
    if "emission_factor" not in ss:
        ss.emission_factor = 0.251  # sensible default; adjust to your baseline
    if "trips_data" not in ss:
        ss.trips_data = pd.DataFrame(columns=[
            'date','customer','from_location','to_location',
            'tons_loaded','truck_type','plate_number','distance_km'
        ])
    if "energy_consumption" not in ss:
        ss.energy_consumption = pd.DataFrame(columns=['plate_number','period','kwh_per_km'])
    if "locations_data" not in ss:
        ss.locations_data = pd.DataFrame(columns=['location_name','coordinates'])
    if "routes_data" not in ss:
        ss.routes_data = pd.DataFrame(columns=['from_location_name','to_location_name','km_distance','source'])

_ensure_state()

# ---------- Page lead-in (no st.title—header already injected) ----------
st.markdown("### Current System Data")

col1, col2 = st.columns([2,1], gap="large")

with col1:
    st.markdown("#### Energy Consumption")
    if not st.session_state.energy_consumption.empty:
        st.dataframe(st.session_state.energy_consumption, use_container_width=True)
        # Average efficiency by truck (guard against missing column)
        df_ec = st.session_state.energy_consumption
        if {"plate_number","kwh_per_km"}.issubset(df_ec.columns):
            avg_eff = (df_ec
                       .dropna(subset=["plate_number","kwh_per_km"])
                       .groupby("plate_number", as_index=False)["kwh_per_km"]
                       .mean())
            st.markdown("**Average kWh/km by Truck**")
            st.dataframe(avg_eff, use_container_width=True)
        else:
            st.info("Columns 'plate_number' and/or 'kwh_per_km' not found.")
    else:
        st.info("No energy consumption data available.")

with col2:
    st.markdown("#### Emission Factor")
    emission_factor = st.number_input(
        "CO₂ Emission Factor (kg CO₂/kWh)",
        min_value=0.0, max_value=2.0,
        value=float(st.session_state.emission_factor),
        step=0.01,
        help="Monthly emission factor used for CO₂ calculations"
    )
    if emission_factor != st.session_state.emission_factor:
        st.session_state.emission_factor = emission_factor
        st.success("Emission factor updated!")
    st.write(f"**Current Emission Factor:** {st.session_state.emission_factor:.3f} kg CO₂/kWh")

# ---------- Data Import ----------
st.markdown("### Import Data")
tab1, tab2, tab3, tab4 = st.tabs(["Trip Data", "Energy Consumption", "Locations", "Routes"])

# --- Trip Data ---
with tab1:
    st.markdown("#### Import Trip Data from TMS")
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.write("**Standard CSV format columns:**")
        st.write("- date\n- customer\n- from_location\n- to_location\n- tons_loaded\n- truck_type\n- plate_number\n- distance_km (optional)")
        st.write("**TMS Excel format (auto-mapped):**")
        st.write(
            "- Head Plate Number → plate_number\n"
            "- Customer → customer\n"
            "- Orgin → from_location\n"
            "- Destination → to_location\n"
            "- Total Weight → tons_loaded\n"
            "- Departure Date → date\n"
            "- Trip KM → distance_km\n"
            "- Req. Truck Type → truck_type"
        )

    with c2:
        template_data = pd.DataFrame({
            'date': [datetime.now().strftime('%Y-%m-%d')],
            'customer': ['Example Customer'],
            'from_location': ['Warehouse A'],
            'to_location': ['Customer Site B'],
            'tons_loaded': [15.5],
            'truck_type': ['Electric'],
            'plate_number': ['ABC123'],
            'distance_km': [45.2]
        })
        st.download_button(
            label="📥 Download Trip Template CSV",
            data=template_data.to_csv(index=False),
            file_name="trip_data_template.csv",
            mime="text/csv"
        )

    uploaded_trips = st.file_uploader(
        "Upload Trip Data",
        type=['csv', 'xlsx', 'xls'],
        key="trips_upload"
    )

    if uploaded_trips is not None:
        try:
            if uploaded_trips.name.lower().endswith('.csv'):
                df = pd.read_csv(uploaded_trips)
            else:
                df = pd.read_excel(uploaded_trips)

                # Heuristic: detect TMS header row in first few rows
                tms_cols = {'Head Plate Number','Customer','Orgin','Destination','Total Weight','Departure Date','Trip KM','Req. Truck Type'}
                header_row_idx = None
                for i in range(min(5, len(df))):
                    row_vals = set(str(v).strip() for v in list(df.iloc[i].values))
                    if len(tms_cols.intersection(row_vals)) >= 3:
                        header_row_idx = i
                        break

                if header_row_idx is not None:
                    df.columns = df.iloc[header_row_idx]
                    df = df.drop(range(header_row_idx + 1)).reset_index(drop=True)
                    mapping = {
                        'Head Plate Number': 'plate_number',
                        'Customer': 'customer',
                        'Orgin': 'from_location',
                        'Destination': 'to_location',
                        'Total Weight': 'tons_loaded',
                        'Departure Date': 'date',
                        'Trip KM': 'distance_km',
                        'Req. Truck Type': 'truck_type'
                    }
                    df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
                    keep_cols = [c for c in mapping.values() if c in df.columns]
                    if keep_cols:
                        df = df[keep_cols]
                    st.info("✅ Detected TMS format – columns auto-mapped.")

            st.write("**Preview of uploaded data:**")
            st.dataframe(df.head(), use_container_width=True)

            required_cols = ['date','customer','from_location','to_location','tons_loaded','truck_type','plate_number']
            essential_cols = ['customer','from_location','to_location','plate_number']

            missing_required = [c for c in required_cols if c not in df.columns]
            if missing_required:
                st.warning(f"Missing columns: {missing_required}. Import will proceed with available data where possible.")

            missing_essential = [c for c in essential_cols if c not in df.columns]
            if missing_essential:
                st.error(f"Missing essential columns: {missing_essential}. Cannot import.")
            else:
                # Validation
                total_rows = len(df)
                available_required = [c for c in required_cols if c in df.columns]
                for c in available_required:
                    if df[c].isna().any():
                        st.warning(f"Column '{c}' has missing values.")

                # Dates
                if 'date' in df.columns:
                    with st.spinner("Parsing dates..."):
                        df['date'] = pd.to_datetime(df['date'], errors='coerce')
                else:
                    df['date'] = pd.Timestamp.now().date()
                    st.warning("No 'date' column found – using current date.")

                valid_rows = len(df.dropna(subset=essential_cols))
                m1, m2, m3 = st.columns(3)
                m1.metric("Total Rows", total_rows)
                m2.metric("Valid Rows", valid_rows)
                m3.metric("Invalid Rows", total_rows - valid_rows)

                if st.button("Import Trip Data", type="primary"):
                    clean_df = df.dropna(subset=essential_cols).copy()

                    # Defaults
                    defaults = {'tons_loaded': 0.0, 'truck_type': 'Electric', 'distance_km': 0.0}
                    for k, v in defaults.items():
                        if k not in clean_df.columns:
                            clean_df[k] = v

                    # Final column order
                    final_cols = ['date','customer','from_location','to_location','tons_loaded','truck_type','plate_number','distance_km']
                    for c in final_cols:
                        if c not in clean_df.columns:
                            clean_df[c] = defaults.get(c, '')

                    # Types
                    clean_df['tons_loaded'] = pd.to_numeric(clean_df['tons_loaded'], errors='coerce').fillna(0.0)
                    clean_df['distance_km'] = pd.to_numeric(clean_df['distance_km'], errors='coerce').fillna(0.0)
                    for s in ['customer','from_location','to_location','truck_type','plate_number']:
                        clean_df[s] = clean_df[s].astype(str).replace('nan','')

                    clean_df = clean_df[final_cols]

                    st.session_state.trips_data = pd.concat(
                        [st.session_state.trips_data, clean_df],
                        ignore_index=True
                    )
                    st.success(f"Successfully imported {len(clean_df)} trip records!")
                    st.rerun()

        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- Energy Consumption ---
with tab2:
    st.markdown("#### Import Energy Consumption Data")
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.write("**Required columns:**")
        st.write("- plate_number\n- period (YYYY-MM)\n- kwh_per_km")

    with c2:
        energy_template = pd.DataFrame({
            'plate_number': ['ABC123','DEF456'],
            'period': ['2024-01','2024-01'],
            'kwh_per_km': [1.2, 1.1]
        })
        st.download_button(
            label="📥 Download Energy Template CSV",
            data=energy_template.to_csv(index=False),
            file_name="energy_consumption_template.csv",
            mime="text/csv"
        )

    uploaded_energy = st.file_uploader(
        "Upload Energy Consumption Data",
        type=['csv','xlsx','xls'],
        key="energy_upload"
    )

    if uploaded_energy is not None:
        try:
            df = pd.read_csv(uploaded_energy) if uploaded_energy.name.lower().endswith('.csv') else pd.read_excel(uploaded_energy)
            st.write("**Preview of uploaded data:**")
            st.dataframe(df.head(), use_container_width=True)

            required_cols = ['plate_number','period','kwh_per_km']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.error(f"Missing required columns: {missing}")
            else:
                if st.button("Import Energy Data", type="primary"):
                    clean_df = df.dropna(subset=required_cols).copy()
                    st.session_state.energy_consumption = pd.concat(
                        [st.session_state.energy_consumption, clean_df],
                        ignore_index=True
                    )
                    st.success(f"Successfully imported {len(clean_df)} energy consumption records!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- Locations ---
with tab3:
    st.markdown("#### Import Locations Data")
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.write("**Required columns:**")
        st.write("- location_name\n- coordinates (lat,lng)")

    with c2:
        locations_template = pd.DataFrame({
            'location_name': ['Warehouse A','Customer Site B'],
            'coordinates': ['40.7128,-74.0060','40.7589,-73.9851']
        })
        st.download_button(
            label="📥 Download Locations Template CSV",
            data=locations_template.to_csv(index=False),
            file_name="locations_template.csv",
            mime="text/csv"
        )

    uploaded_locations = st.file_uploader(
        "Upload Locations Data",
        type=['csv','xlsx','xls'],
        key="locations_upload"
    )

    if uploaded_locations is not None:
        try:
            df = pd.read_csv(uploaded_locations) if uploaded_locations.name.lower().endswith('.csv') else pd.read_excel(uploaded_locations)
            st.dataframe(df.head(), use_container_width=True)

            required_cols = ['location_name','coordinates']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.error(f"Missing required columns: {missing}")
            else:
                if st.button("Import Locations", type="primary"):
                    clean_df = df.dropna(subset=required_cols).copy()
                    st.session_state.locations_data = (
                        pd.concat([st.session_state.locations_data, clean_df], ignore_index=True)
                          .drop_duplicates(subset=['location_name'], keep='last')
                    )
                    st.success(f"Successfully imported {len(clean_df)} locations!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- Routes ---
with tab4:
    st.markdown("#### Import Routes Data")
    c1, c2 = st.columns(2, gap="large")

    with c1:
        st.write("**Required columns:**")
        st.write("- from_location_name\n- to_location_name\n- km_distance\n- source")

    with c2:
        routes_template = pd.DataFrame({
            'from_location_name': ['Warehouse A','Customer Site B'],
            'to_location_name': ['Customer Site B','Warehouse A'],
            'km_distance': [45.2, 45.2],
            'source': ['Manual','Manual']
        })
        st.download_button(
            label="📥 Download Routes Template CSV",
            data=routes_template.to_csv(index=False),
            file_name="routes_template.csv",
            mime="text/csv"
        )

    uploaded_routes = st.file_uploader(
        "Upload Routes Data",
        type=['csv','xlsx','xls'],
        key="routes_upload"
    )

    if uploaded_routes is not None:
        try:
            df = pd.read_csv(uploaded_routes) if uploaded_routes.name.lower().endswith('.csv') else pd.read_excel(uploaded_routes)
            st.dataframe(df.head(), use_container_width=True)

            required_cols = ['from_location_name','to_location_name','km_distance','source']
            missing = [c for c in required_cols if c not in df.columns]
            if missing:
                st.error(f"Missing required columns: {missing}")
            else:
                if st.button("Import Routes", type="primary"):
                    clean_df = df.dropna(subset=required_cols).copy()
                    st.session_state.routes_data = pd.concat(
                        [st.session_state.routes_data, clean_df],
                        ignore_index=True
                    )
                    st.success(f"Successfully imported {len(clean_df)} routes!")
                    st.rerun()
        except Exception as e:
            st.error(f"Error reading file: {e}")

# ---------- Data Summary ----------
st.markdown("### Data Summary")
s1, s2, s3, s4 = st.columns(4)
s1.metric("Trip Records", len(st.session_state.trips_data))
s2.metric("Energy Records", len(st.session_state.energy_consumption))
s3.metric("Locations", len(st.session_state.locations_data))
s4.metric("Routes", len(st.session_state.routes_data))

# ---------- Data Management ----------
st.markdown("### Data Management")
with st.expander("⚠️ Clear Data", expanded=False):
    st.warning("This action cannot be undone!")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("Clear Trip Data", type="secondary"):
            st.session_state.trips_data = st.session_state.trips_data.iloc[0:0]
            st.success("Trip data cleared!")
            st.rerun()
    with c2:
        if st.button("Clear Energy Data", type="secondary"):
            st.session_state.energy_consumption = st.session_state.energy_consumption.iloc[0:0]
            st.success("Energy data cleared!")
            st.rerun()
    with c3:
        if st.button("Clear Locations", type="secondary"):
            st.session_state.locations_data = st.session_state.locations_data.iloc[0:0]
            st.success("Locations cleared!")
            st.rerun()
    with c4:
        if st.button("Clear Routes", type="secondary"):
            st.session_state.routes_data = st.session_state.routes_data.iloc[0:0]
            st.success("Routes cleared!")
            st.rerun()
