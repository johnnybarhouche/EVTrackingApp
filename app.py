import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="EV Truck Performance Tracker",
    page_icon="🚛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'trips_data' not in st.session_state:
    st.session_state.trips_data = pd.DataFrame(columns=[
        'date', 'customer', 'from_location', 'to_location', 
        'tons_loaded', 'truck_type', 'plate_number', 'distance_km'
    ])

if 'trucks_data' not in st.session_state:
    st.session_state.trucks_data = pd.DataFrame(columns=[
        'plate', 'make', 'kwh_per_km', 'total_kwh', 'total_km', 
        'total_trips', 'total_tkm', 'kg_co2', 'kwh_per_tkm', 
        'kg_co2_per_tkm', 'kg_co2_per_km'
    ])

if 'locations_data' not in st.session_state:
    st.session_state.locations_data = pd.DataFrame(columns=[
        'location_name', 'coordinates'
    ])

if 'routes_data' not in st.session_state:
    st.session_state.routes_data = pd.DataFrame(columns=[
        'from_location_name', 'to_location_name', 'km_distance', 'source'
    ])

if 'energy_consumption' not in st.session_state:
    st.session_state.energy_consumption = pd.DataFrame(columns=[
        'plate_number', 'period', 'kwh_per_km'
    ])

if 'emission_factor' not in st.session_state:
    st.session_state.emission_factor = 0.5  # Default KgCO2/kWh

# Main page content
st.title("🚛 EV Truck Performance Tracker")

st.markdown("""
### Welcome to the EV Truck Performance Tracking System

This application helps you track and analyze the performance of your electric vehicle fleet. 
Use the navigation menu to access different sections:

- **Dashboard**: Overview of key metrics and performance indicators
- **Trips**: Detailed trip data and management
- **Trucks**: Fleet information and performance metrics
- **Locations**: Manage pickup and delivery locations
- **Routes**: Route management and distance tracking
- **Data & Import**: Import data from TMS and manage system data
- **Export**: Generate reports and export data
- **Debug**: System diagnostics and data validation

### Getting Started

1. **Import your data** using the Data & Import section
2. **Set up locations** in the Locations section
3. **Configure routes** in the Routes section
4. **View your dashboard** for performance insights
5. **Generate reports** using the Export section

Navigate using the sidebar menu to get started.
""")

# Sidebar information
with st.sidebar:
    st.header("Navigation")
    st.markdown("Use the pages above to navigate through the application.")
    
    st.header("Quick Stats")
    if not st.session_state.trips_data.empty:
        total_trips = len(st.session_state.trips_data)
        total_trucks = st.session_state.trips_data['plate_number'].nunique()
        st.metric("Total Trips", total_trips)
        st.metric("Active Trucks", total_trucks)
    else:
        st.info("Import trip data to see quick stats")
    
    st.header("System Status")
    st.success("System Online")
    st.info(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
