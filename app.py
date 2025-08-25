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

# Custom CSS styling to match DSV interface
st.markdown("""
<style>
    /* Import DSV styling */
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700&display=swap');
    
    /* Main app background */
    .stApp {
        background-color: #f5f5f5;
        font-family: 'Roboto', sans-serif;
    }
    
    /* Sidebar styling - DSV dark blue */
    .css-1d391kg, .css-1oe6wy4, section[data-testid="stSidebar"] {
        background-color: #1f4e79 !important;
    }
    
    /* Sidebar navigation text */
    .css-1d391kg .css-10trblm, 
    .css-1oe6wy4 .css-10trblm,
    section[data-testid="stSidebar"] .css-10trblm {
        color: white !important;
    }
    
    /* Navigation links in sidebar */
    .css-1d391kg a, .css-1oe6wy4 a {
        color: white !important;
        text-decoration: none !important;
    }
    
    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-left: 2rem;
        padding-right: 2rem;
        background-color: #f5f5f5;
    }
    
    /* DSV-style header with logo area */
    .main-header {
        background-color: #1f4e79;
        color: white;
        padding: 1rem 2rem;
        margin: -2rem -2rem 2rem -2rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    /* Table headers - dark blue background */
    .stDataFrame thead tr th,
    .stDataFrame thead th,
    thead tr th {
        background-color: #1f4e79 !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 12px !important;
    }
    
    /* Table styling */
    .stDataFrame table {
        border: 1px solid #ddd;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Table body styling */
    .stDataFrame tbody tr:nth-child(even) {
        background-color: #f8f9fa;
    }
    
    .stDataFrame tbody tr:hover {
        background-color: #e3f2fd;
    }
    
    /* Metrics styling - card design */
    [data-testid="metric-container"] {
        background: white;
        border: 1px solid #e0e0e0;
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: box-shadow 0.3s ease;
    }
    
    [data-testid="metric-container"]:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Button styling - DSV blue */
    .stButton > button {
        background-color: #1f4e79;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        font-size: 14px;
        transition: background-color 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #163a5f;
        color: white;
        box-shadow: 0 2px 8px rgba(31, 78, 121, 0.3);
    }
    
    /* Header styling */
    h1 {
        color: #1f4e79 !important;
        font-weight: 600 !important;
        font-size: 2.5rem !important;
        margin-bottom: 1rem !important;
    }
    
    h2 {
        color: #1f4e79 !important;
        font-weight: 500 !important;
        font-size: 1.8rem !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
    }
    
    h3 {
        color: #1f4e79 !important;
        font-weight: 500 !important;
        font-size: 1.4rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    /* Navigation menu styling */
    .css-1vq4p4l, .css-12w0qpk {
        background-color: #1f4e79 !important;
    }
    
    /* Selected page indicator */
    .css-1vq4p4l .css-1rs6os {
        background-color: rgba(255,255,255,0.2) !important;
        border-radius: 4px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #e8e8e8;
        border-radius: 6px;
        font-weight: 500;
    }
    
    /* Success/info/warning messages */
    .stAlert {
        border-radius: 6px;
        border-left: 4px solid #1f4e79;
    }
    
    /* Form styling */
    .stForm {
        background: white;
        padding: 1.5rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div > div {
        border: 1px solid #d0d0d0;
        border-radius: 4px;
        padding: 0.5rem;
    }
    
    /* Charts container */
    .js-plotly-plot {
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# DSV-style header
st.markdown("""
<div class="main-header">
    <div style="display: flex; align-items: center;">
        <div style="background: white; color: #1f4e79; padding: 0.5rem 1rem; border-radius: 4px; font-weight: bold; margin-right: 1rem;">
            DSV
        </div>
        <h1 style="color: white; margin: 0; font-size: 1.8rem;">EV Truck Performance Tracker</h1>
    </div>
    <div style="color: white; font-size: 0.9rem;">
        Sustainability Dashboard
    </div>
</div>
""", unsafe_allow_html=True)

# Main page content
st.markdown("## Dashboard Overview")

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
