import streamlit as st
import pandas as pd
import json
from datetime import datetime

st.set_page_config(page_title="Debug", page_icon="🔧", layout="wide")

st.title("🔧 System Debug & Diagnostics")

# System Information
st.header("System Information")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Python Version", "3.x")
    st.metric("Streamlit Version", st.__version__)

with col2:
    st.metric("Current Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    st.metric("Session ID", str(id(st.session_state))[-8:])

with col3:
    memory_usage = sum(len(str(v)) for v in st.session_state.values() if hasattr(v, '__len__'))
    st.metric("Memory Usage (approx)", f"{memory_usage:,} chars")

# Data Status
st.header("Data Status")

data_status = {
    "Trip Data": {
        "records": len(st.session_state.trips_data),
        "columns": list(st.session_state.trips_data.columns) if not st.session_state.trips_data.empty else [],
        "memory_size": st.session_state.trips_data.memory_usage(deep=True).sum() if not st.session_state.trips_data.empty else 0
    },
    "Energy Consumption": {
        "records": len(st.session_state.energy_consumption),
        "columns": list(st.session_state.energy_consumption.columns) if not st.session_state.energy_consumption.empty else [],
        "memory_size": st.session_state.energy_consumption.memory_usage(deep=True).sum() if not st.session_state.energy_consumption.empty else 0
    },
    "Locations": {
        "records": len(st.session_state.locations_data),
        "columns": list(st.session_state.locations_data.columns) if not st.session_state.locations_data.empty else [],
        "memory_size": st.session_state.locations_data.memory_usage(deep=True).sum() if not st.session_state.locations_data.empty else 0
    },
    "Routes": {
        "records": len(st.session_state.routes_data),
        "columns": list(st.session_state.routes_data.columns) if not st.session_state.routes_data.empty else [],
        "memory_size": st.session_state.routes_data.memory_usage(deep=True).sum() if not st.session_state.routes_data.empty else 0
    }
}

for data_type, info in data_status.items():
    with st.expander(f"{data_type} - {info['records']} records"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Columns:**")
            if info['columns']:
                for col in info['columns']:
                    st.write(f"- {col}")
            else:
                st.write("No data")
        
        with col2:
            st.metric("Memory Usage", f"{info['memory_size']:,} bytes")
            st.metric("Records", info['records'])

# Data Validation
st.header("Data Validation")

validation_results = []

# Validate trip data
if not st.session_state.trips_data.empty:
    trips_df = st.session_state.trips_data
    
    # Check for missing values
    missing_values = trips_df.isnull().sum()
    if missing_values.any():
        for col, missing_count in missing_values[missing_values > 0].items():
            validation_results.append({
                "Type": "Warning",
                "Table": "Trip Data",
                "Issue": f"Missing values in column '{col}'",
                "Count": missing_count
            })
    
    # Check date format
    try:
        pd.to_datetime(trips_df['date'])
        validation_results.append({
            "Type": "Success",
            "Table": "Trip Data",
            "Issue": "Date format validation",
            "Count": "Passed"
        })
    except:
        validation_results.append({
            "Type": "Error",
            "Table": "Trip Data", 
            "Issue": "Invalid date format",
            "Count": "Failed"
        })
    
    # Check for negative values
    if 'distance_km' in trips_df.columns:
        negative_distances = (trips_df['distance_km'] < 0).sum()
        if negative_distances > 0:
            validation_results.append({
                "Type": "Error",
                "Table": "Trip Data",
                "Issue": "Negative distances found",
                "Count": negative_distances
            })
    
    if 'tons_loaded' in trips_df.columns:
        negative_tons = (trips_df['tons_loaded'] < 0).sum()
        if negative_tons > 0:
            validation_results.append({
                "Type": "Error",
                "Table": "Trip Data",
                "Issue": "Negative cargo weights found",
                "Count": negative_tons
            })

# Validate energy consumption data
if not st.session_state.energy_consumption.empty:
    energy_df = st.session_state.energy_consumption
    
    # Check for unrealistic efficiency values
    if 'kwh_per_km' in energy_df.columns:
        high_efficiency = (energy_df['kwh_per_km'] > 5).sum()
        low_efficiency = (energy_df['kwh_per_km'] < 0.1).sum()
        
        if high_efficiency > 0:
            validation_results.append({
                "Type": "Warning",
                "Table": "Energy Data",
                "Issue": "High energy consumption (>5 kWh/km)",
                "Count": high_efficiency
            })
        
        if low_efficiency > 0:
            validation_results.append({
                "Type": "Warning", 
                "Table": "Energy Data",
                "Issue": "Low energy consumption (<0.1 kWh/km)",
                "Count": low_efficiency
            })

# Validate location coordinates
if not st.session_state.locations_data.empty:
    locations_df = st.session_state.locations_data
    
    invalid_coords = 0
    for coord in locations_df['coordinates']:
        try:
            if pd.notna(coord):
                lat, lng = map(float, str(coord).split(','))
                if not (-90 <= lat <= 90 and -180 <= lng <= 180):
                    invalid_coords += 1
        except:
            invalid_coords += 1
    
    if invalid_coords > 0:
        validation_results.append({
            "Type": "Error",
            "Table": "Locations",
            "Issue": "Invalid coordinate format or values",
            "Count": invalid_coords
        })

# Display validation results
if validation_results:
    validation_df = pd.DataFrame(validation_results)
    
    # Color code by type
    def color_type(val):
        if val == 'Error':
            return 'background-color: #ffebee'
        elif val == 'Warning':
            return 'background-color: #fff3e0'
        elif val == 'Success':
            return 'background-color: #e8f5e8'
        return ''
    
    styled_df = validation_df.style.applymap(color_type, subset=['Type'])
    st.dataframe(styled_df, use_container_width=True)
else:
    st.success("No validation issues found!")

# Session State Inspector
st.header("Session State Inspector")
with st.expander("View All Session State Variables"):
    for key, value in st.session_state.items():
        st.write(f"**{key}:**")
        if isinstance(value, pd.DataFrame):
            st.write(f"DataFrame with {len(value)} rows and {len(value.columns)} columns")
            if not value.empty:
                st.dataframe(value.head())
        else:
            st.write(value)
        st.write("---")

# Data Export for Debugging
st.header("Debug Data Export")
if st.button("Export Debug Information"):
    debug_info = {
        "timestamp": datetime.now().isoformat(),
        "data_status": data_status,
        "validation_results": validation_results,
        "emission_factor": st.session_state.emission_factor,
        "session_keys": list(st.session_state.keys())
    }
    
    debug_json = json.dumps(debug_info, indent=2, default=str)
    st.download_button(
        label="Download Debug Report",
        data=debug_json,
        file_name=f"debug_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )

# Performance Metrics
st.header("Performance Metrics")

col1, col2, col3 = st.columns(3)

with col1:
    total_records = sum(len(getattr(st.session_state, key, [])) for key in ['trips_data', 'energy_consumption', 'locations_data', 'routes_data'])
    st.metric("Total Records", total_records)

with col2:
    unique_trucks = st.session_state.trips_data['plate_number'].nunique() if not st.session_state.trips_data.empty else 0
    st.metric("Unique Trucks", unique_trucks)

with col3:
    unique_customers = st.session_state.trips_data['customer'].nunique() if not st.session_state.trips_data.empty else 0
    st.metric("Unique Customers", unique_customers)

# System Health Check
st.header("System Health Check")

health_checks = []

# Check data integrity
if not st.session_state.trips_data.empty and not st.session_state.energy_consumption.empty:
    trip_trucks = set(st.session_state.trips_data['plate_number'].unique())
    energy_trucks = set(st.session_state.energy_consumption['plate_number'].unique())
    
    trucks_without_energy = trip_trucks - energy_trucks
    if trucks_without_energy:
        health_checks.append({
            "Status": "Warning",
            "Check": "Data Integrity",
            "Message": f"Trucks without energy data: {', '.join(trucks_without_energy)}"
        })
    else:
        health_checks.append({
            "Status": "OK",
            "Check": "Data Integrity", 
            "Message": "All trucks have energy consumption data"
        })

# Check location coverage
if not st.session_state.trips_data.empty and not st.session_state.locations_data.empty:
    trip_locations = set()
    if 'from_location' in st.session_state.trips_data.columns:
        trip_locations.update(st.session_state.trips_data['from_location'].dropna().unique())
    if 'to_location' in st.session_state.trips_data.columns:
        trip_locations.update(st.session_state.trips_data['to_location'].dropna().unique())
    
    defined_locations = set(st.session_state.locations_data['location_name'].unique())
    missing_locations = trip_locations - defined_locations
    
    if missing_locations:
        health_checks.append({
            "Status": "Warning",
            "Check": "Location Coverage",
            "Message": f"Locations used in trips but not defined: {', '.join(list(missing_locations)[:5])}"
        })
    else:
        health_checks.append({
            "Status": "OK",
            "Check": "Location Coverage",
            "Message": "All trip locations are defined"
        })

# Display health checks
if health_checks:
    health_df = pd.DataFrame(health_checks)
    
    def color_status(val):
        if val == 'Warning':
            return 'background-color: #fff3e0'
        elif val == 'OK':
            return 'background-color: #e8f5e8'
        return ''
    
    styled_health = health_df.style.applymap(color_status, subset=['Status'])
    st.dataframe(styled_health, use_container_width=True)
else:
    st.info("No health checks configured yet.")

# Manual data correction tools
st.header("Data Correction Tools")

with st.expander("Manual Data Corrections"):
    st.subheader("Update Emission Factor")
    new_emission_factor = st.number_input(
        "New Emission Factor (kg CO2/kWh)",
        min_value=0.0,
        max_value=2.0,
        value=st.session_state.emission_factor,
        step=0.01
    )
    
    if st.button("Update Emission Factor"):
        st.session_state.emission_factor = new_emission_factor
        st.success("Emission factor updated!")
        st.rerun()
    
    st.subheader("Remove Duplicate Trips")
    if not st.session_state.trips_data.empty:
        duplicates = st.session_state.trips_data.duplicated().sum()
        st.write(f"Found {duplicates} duplicate trips")
        
        if duplicates > 0 and st.button("Remove Duplicate Trips"):
            st.session_state.trips_data = st.session_state.trips_data.drop_duplicates()
            st.success(f"Removed {duplicates} duplicate trips!")
            st.rerun()
