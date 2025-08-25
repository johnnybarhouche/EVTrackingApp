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

# Initialize with default truck data
if 'default_trucks_loaded' not in st.session_state:
    default_trucks = pd.DataFrame({
        'plate_number': ['45211', '73619', '72738', '27681', '29179', '29150', '29176', '29142', '45282'],
        'period': ['2024-01'] * 9,
        'kwh_per_km': [1.2, 1.1, 1.3, 1.15, 1.08, 1.25, 1.2, 1.1, 1.4]
    })
    
    # Initialize truck master data
    truck_master = pd.DataFrame({
        'serial': ['9/45211 DSV HDT EV490', '7/73619 DSV HDT EV490', '17/72738 DSV HDT EV490', 
                  '14/27681 DSV HDT EV490', '11/29179 DSV HDT EV490', '11/29150 DSV HDT EV490',
                  '11/29176 DSV HDT EV490', '11/29142 DSV HDT EV490', '19/45282 DSV LDT ST4200'],
        'plate': ['45211', '73619', '72738', '27681', '29179', '29150', '29176', '29142', '45282'],
        'brand': ['SANY'] * 9,
        'vin': ['LFCAH96W1P3002623', 'LFCAH96W6P3004111', 'LFCAH96WXP3004113', 
               'LFCAH96W8P3004109', 'LFCAH96W8P3004112', 'LFCAH96W3P3004115',
               'LFCAH96W4P3004110', 'LFCAH96W7P3003999', 'LFXDB22P4P3080364'],
        'year': [2024] * 9,
        'model': ['Truck/Heavy Duty Truck/EV'] * 8 + ['Truck/Light Duty Truck/EV'],
        'id': ['51230421020046', '51230421020038', '51230725020010', '51230725020058',
               '51230725020050', '51230725020014', '51230421020022', '51230725020078', '51230725020100']
    })
    
    if st.session_state.energy_consumption.empty:
        st.session_state.energy_consumption = default_trucks
    
    st.session_state.truck_master_data = truck_master
    st.session_state.default_trucks_loaded = True
    
    # Load sample trip data if available
    try:
        if st.session_state.trips_data.empty:
            sample_trips = pd.read_csv('data/sample_trips.csv')
            sample_trips['date'] = pd.to_datetime(sample_trips['date'])
            # Ensure numeric types
            sample_trips['tons_loaded'] = pd.to_numeric(sample_trips['tons_loaded'], errors='coerce').fillna(0.0)
            sample_trips['distance_km'] = pd.to_numeric(sample_trips['distance_km'], errors='coerce').fillna(0.0)
            st.session_state.trips_data = sample_trips
    except:
        pass  # No sample data available

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
