import streamlit as st
import pandas as pd
import io
from datetime import datetime

st.set_page_config(page_title="Data & Import", page_icon="📊", layout="wide")

st.title("📊 Data & Import")

# Display current data configuration
st.subheader("Current System Data")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Energy Consumption")
    if not st.session_state.energy_consumption.empty:
        st.dataframe(st.session_state.energy_consumption, use_container_width=True)
        
        # Calculate average efficiency by truck
        avg_efficiency = st.session_state.energy_consumption.groupby('plate_number')['kwh_per_km'].mean()
        st.write("**Average kWh/km by Truck:**")
        st.dataframe(avg_efficiency.reset_index(), use_container_width=True)
    else:
        st.info("No energy consumption data available")

with col2:
    st.subheader("Emission Factor")
    emission_factor = st.number_input(
        "CO2 Emission Factor (kg CO2/kWh)",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.emission_factor,
        step=0.01,
        help="Monthly emission factor used for CO2 calculations"
    )
    
    if emission_factor != st.session_state.emission_factor:
        st.session_state.emission_factor = emission_factor
        st.success("Emission factor updated!")
    
    st.write(f"**Current Emission Factor:** {st.session_state.emission_factor} kg CO2/kWh")

# Data Import Section
st.header("Import Data")

# Create tabs for different import types
tab1, tab2, tab3, tab4 = st.tabs(["Trip Data", "Energy Consumption", "Locations", "Routes"])

with tab1:
    st.subheader("Import Trip Data from TMS")
    
    # Download template
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Required columns:**")
        st.write("- date")
        st.write("- customer") 
        st.write("- from_location")
        st.write("- to_location")
        st.write("- tons_loaded")
        st.write("- truck_type")
        st.write("- plate_number")
        st.write("- distance_km (optional)")
    
    with col2:
        # Create template file
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
        
        template_csv = template_data.to_csv(index=False)
        st.download_button(
            label="📥 Download Trip Template CSV",
            data=template_csv,
            file_name="trip_data_template.csv",
            mime="text/csv"
        )
    
    # Upload file
    uploaded_trips = st.file_uploader(
        "Upload Trip Data",
        type=['csv', 'xlsx', 'xls'],
        key="trips_upload"
    )
    
    if uploaded_trips is not None:
        try:
            if uploaded_trips.name.endswith('.csv'):
                df = pd.read_csv(uploaded_trips)
            else:
                df = pd.read_excel(uploaded_trips)
            
            st.write("**Preview of uploaded data:**")
            st.dataframe(df.head())
            
            # Validate required columns
            required_cols = ['date', 'customer', 'from_location', 'to_location', 
                           'tons_loaded', 'truck_type', 'plate_number']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Missing required columns: {missing_cols}")
            else:
                # Data validation
                valid_rows = 0
                total_rows = len(df)
                
                # Check for missing values in required fields
                for col in required_cols:
                    if df[col].isna().any():
                        st.warning(f"Column '{col}' has missing values")
                
                # Try to parse dates
                try:
                    df['date'] = pd.to_datetime(df['date'])
                    valid_rows = len(df.dropna(subset=required_cols))
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Rows", total_rows)
                    with col2:
                        st.metric("Valid Rows", valid_rows)
                    with col3:
                        st.metric("Invalid Rows", total_rows - valid_rows)
                    
                    if st.button("Import Trip Data", type="primary"):
                        # Clean data before import
                        clean_df = df.dropna(subset=required_cols).copy()
                        
                        # If distance_km is not provided, set to 0 (will be calculated later)
                        if 'distance_km' not in clean_df.columns:
                            clean_df['distance_km'] = 0
                        
                        st.session_state.trips_data = pd.concat([
                            st.session_state.trips_data,
                            clean_df
                        ], ignore_index=True)
                        
                        st.success(f"Successfully imported {len(clean_df)} trip records!")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Date parsing error: {str(e)}")
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

with tab2:
    st.subheader("Import Energy Consumption Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Required columns:**")
        st.write("- plate_number")
        st.write("- period (YYYY-MM format)")
        st.write("- kwh_per_km")
    
    with col2:
        # Create template
        energy_template = pd.DataFrame({
            'plate_number': ['ABC123', 'DEF456'],
            'period': ['2024-01', '2024-01'],
            'kwh_per_km': [1.2, 1.1]
        })
        
        energy_csv = energy_template.to_csv(index=False)
        st.download_button(
            label="📥 Download Energy Template CSV",
            data=energy_csv,
            file_name="energy_consumption_template.csv",
            mime="text/csv"
        )
    
    uploaded_energy = st.file_uploader(
        "Upload Energy Consumption Data",
        type=['csv', 'xlsx', 'xls'],
        key="energy_upload"
    )
    
    if uploaded_energy is not None:
        try:
            if uploaded_energy.name.endswith('.csv'):
                df = pd.read_csv(uploaded_energy)
            else:
                df = pd.read_excel(uploaded_energy)
            
            st.write("**Preview of uploaded data:**")
            st.dataframe(df.head())
            
            required_cols = ['plate_number', 'period', 'kwh_per_km']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Missing required columns: {missing_cols}")
            else:
                if st.button("Import Energy Data", type="primary"):
                    clean_df = df.dropna(subset=required_cols).copy()
                    
                    st.session_state.energy_consumption = pd.concat([
                        st.session_state.energy_consumption,
                        clean_df
                    ], ignore_index=True)
                    
                    st.success(f"Successfully imported {len(clean_df)} energy consumption records!")
                    st.rerun()
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

with tab3:
    st.subheader("Import Locations Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Required columns:**")
        st.write("- location_name")
        st.write("- coordinates (lat,lng format)")
    
    with col2:
        locations_template = pd.DataFrame({
            'location_name': ['Warehouse A', 'Customer Site B'],
            'coordinates': ['40.7128,-74.0060', '40.7589,-73.9851']
        })
        
        locations_csv = locations_template.to_csv(index=False)
        st.download_button(
            label="📥 Download Locations Template CSV",
            data=locations_csv,
            file_name="locations_template.csv",
            mime="text/csv"
        )
    
    uploaded_locations = st.file_uploader(
        "Upload Locations Data",
        type=['csv', 'xlsx', 'xls'],
        key="locations_upload"
    )
    
    if uploaded_locations is not None:
        try:
            if uploaded_locations.name.endswith('.csv'):
                df = pd.read_csv(uploaded_locations)
            else:
                df = pd.read_excel(uploaded_locations)
            
            st.dataframe(df.head())
            
            required_cols = ['location_name', 'coordinates']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Missing required columns: {missing_cols}")
            else:
                if st.button("Import Locations", type="primary"):
                    clean_df = df.dropna(subset=required_cols).copy()
                    
                    st.session_state.locations_data = pd.concat([
                        st.session_state.locations_data,
                        clean_df
                    ], ignore_index=True).drop_duplicates(subset=['location_name'], keep='last')
                    
                    st.success(f"Successfully imported {len(clean_df)} locations!")
                    st.rerun()
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

with tab4:
    st.subheader("Import Routes Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Required columns:**")
        st.write("- from_location_name")
        st.write("- to_location_name")
        st.write("- km_distance")
        st.write("- source")
    
    with col2:
        routes_template = pd.DataFrame({
            'from_location_name': ['Warehouse A', 'Customer Site B'],
            'to_location_name': ['Customer Site B', 'Warehouse A'],
            'km_distance': [45.2, 45.2],
            'source': ['Manual', 'Manual']
        })
        
        routes_csv = routes_template.to_csv(index=False)
        st.download_button(
            label="📥 Download Routes Template CSV",
            data=routes_csv,
            file_name="routes_template.csv",
            mime="text/csv"
        )
    
    uploaded_routes = st.file_uploader(
        "Upload Routes Data",
        type=['csv', 'xlsx', 'xls'],
        key="routes_upload"
    )
    
    if uploaded_routes is not None:
        try:
            if uploaded_routes.name.endswith('.csv'):
                df = pd.read_csv(uploaded_routes)
            else:
                df = pd.read_excel(uploaded_routes)
            
            st.dataframe(df.head())
            
            required_cols = ['from_location_name', 'to_location_name', 'km_distance', 'source']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"Missing required columns: {missing_cols}")
            else:
                if st.button("Import Routes", type="primary"):
                    clean_df = df.dropna(subset=required_cols).copy()
                    
                    st.session_state.routes_data = pd.concat([
                        st.session_state.routes_data,
                        clean_df
                    ], ignore_index=True)
                    
                    st.success(f"Successfully imported {len(clean_df)} routes!")
                    st.rerun()
        
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

# Data Summary
st.header("Data Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Trip Records", len(st.session_state.trips_data))

with col2:
    st.metric("Energy Records", len(st.session_state.energy_consumption))

with col3:
    st.metric("Locations", len(st.session_state.locations_data))

with col4:
    st.metric("Routes", len(st.session_state.routes_data))

# Clear data section
st.header("Data Management")
with st.expander("⚠️ Clear Data", expanded=False):
    st.warning("This action cannot be undone!")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Clear Trip Data", type="secondary"):
            st.session_state.trips_data = pd.DataFrame(columns=[
                'date', 'customer', 'from_location', 'to_location', 
                'tons_loaded', 'truck_type', 'plate_number', 'distance_km'
            ])
            st.success("Trip data cleared!")
            st.rerun()
    
    with col2:
        if st.button("Clear Energy Data", type="secondary"):
            st.session_state.energy_consumption = pd.DataFrame(columns=[
                'plate_number', 'period', 'kwh_per_km'
            ])
            st.success("Energy data cleared!")
            st.rerun()
    
    with col3:
        if st.button("Clear Locations", type="secondary"):
            st.session_state.locations_data = pd.DataFrame(columns=[
                'location_name', 'coordinates'
            ])
            st.success("Locations cleared!")
            st.rerun()
    
    with col4:
        if st.button("Clear Routes", type="secondary"):
            st.session_state.routes_data = pd.DataFrame(columns=[
                'from_location_name', 'to_location_name', 'km_distance', 'source'
            ])
            st.success("Routes cleared!")
            st.rerun()
