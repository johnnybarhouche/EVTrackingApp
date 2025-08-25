import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from utils.shared_components import apply_dsv_styling, render_dsv_header

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# Apply consistent DSV styling
apply_dsv_styling()

# Render DSV header
render_dsv_header()

st.title("📊 Dashboard")

# Initialize session state if needed
if 'trips_data' not in st.session_state:
    st.session_state.trips_data = pd.DataFrame()

# Check if data exists
if st.session_state.trips_data.empty:
    st.warning("No trip data available. Please import data from the Data & Import section.")
    st.stop()

# Set default filter values for compatibility
date_range = None
selected_truck = 'All'
selected_client = 'All'

if not st.session_state.trips_data.empty and 'date' in st.session_state.trips_data.columns:
    try:
        st.session_state.trips_data['date'] = pd.to_datetime(st.session_state.trips_data['date'])
        min_date = st.session_state.trips_data['date'].min().date()
        max_date = st.session_state.trips_data['date'].max().date()
        date_range = (min_date, max_date)
    except:
        date_range = None

# Filter data based on selections
filtered_data = st.session_state.trips_data.copy()

if date_range and len(date_range) == 2:
    start_date, end_date = date_range
    filtered_data = filtered_data[
        (filtered_data['date'].dt.date >= start_date) & 
        (filtered_data['date'].dt.date <= end_date)
    ]

if selected_truck != 'All':
    filtered_data = filtered_data[filtered_data['plate_number'] == selected_truck]

if selected_client != 'All':
    filtered_data = filtered_data[filtered_data['customer'] == selected_client]

# Calculate metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_km = filtered_data['distance_km'].sum() if 'distance_km' in filtered_data.columns else 0
    st.metric("Total Kms Driven", f"{total_km:,.0f} km")

with col2:
    total_trips = len(filtered_data)
    st.metric("Number of Trips", f"{total_trips:,}")

with col3:
    if not filtered_data.empty and 'tons_loaded' in filtered_data.columns:
        # Convert to numeric and handle string values
        tons_numeric = pd.to_numeric(filtered_data['tons_loaded'], errors='coerce').fillna(0)
        total_tons = tons_numeric.sum()
        st.metric("Total Tons Transported", f"{total_tons:,.0f} tons")
    else:
        st.metric("Total Tons Transported", "0 tons")

with col4:
    if not filtered_data.empty and 'tons_loaded' in filtered_data.columns:
        # Convert to numeric for average calculation
        tons_numeric = pd.to_numeric(filtered_data['tons_loaded'], errors='coerce').fillna(0)
        avg_load = tons_numeric.mean()
        st.metric("Average Load", f"{avg_load:.1f} tons")
    else:
        st.metric("Average Load", "0 tons")

# Charts section
col1, col2 = st.columns(2)

with col1:
    st.subheader("Number of Trips per Truck")
    if not filtered_data.empty and 'plate_number' in filtered_data.columns:
        trips_per_truck = filtered_data['plate_number'].value_counts()
        fig_trips = px.bar(
            x=trips_per_truck.index,
            y=trips_per_truck.values,
            labels={'x': 'Truck Plate', 'y': 'Number of Trips'},
            color_discrete_sequence=['#002664']
        )
        fig_trips.update_layout(showlegend=False)
        st.plotly_chart(fig_trips, use_container_width=True)
    else:
        st.info("No data available for trips per truck chart")

with col2:
    st.subheader("Kilometers per Truck")
    if not filtered_data.empty and 'plate_number' in filtered_data.columns and 'distance_km' in filtered_data.columns:
        km_per_truck = filtered_data.groupby('plate_number')['distance_km'].sum()
        fig_km = px.bar(
            x=km_per_truck.index,
            y=km_per_truck.values,
            labels={'x': 'Truck Plate', 'y': 'Total Kilometers'},
            color_discrete_sequence=['#4B87E0']
        )
        fig_km.update_layout(showlegend=False)
        st.plotly_chart(fig_km, use_container_width=True)
    else:
        st.info("No data available for kilometers per truck chart")

# Electricity consumption table
st.subheader("Electricity Consumption per Truck")
if not st.session_state.energy_consumption.empty:
    consumption_summary = st.session_state.energy_consumption.groupby('plate_number').agg({
        'kwh_per_km': 'mean'
    }).round(3)

    # Merge with trip data to get total km and calculate total kWh
    if not filtered_data.empty:
        trip_summary = filtered_data.groupby('plate_number').agg({
            'distance_km': 'sum'
        })

        consumption_display = consumption_summary.join(trip_summary, how='outer').fillna(0)
        consumption_display['total_kwh'] = consumption_display['kwh_per_km'] * consumption_display['distance_km']
        consumption_display['co2_emissions'] = consumption_display['total_kwh'] * st.session_state.emission_factor

        consumption_display.columns = ['kWh/km', 'Total km', 'Total kWh', 'CO2 Emissions (kg)']
        st.dataframe(consumption_display, use_container_width=True)
    else:
        st.dataframe(consumption_summary, use_container_width=True)
else:
    st.info("No energy consumption data available. Import energy data in the Data & Import section.")

# Recent trips table
st.subheader("Recent Trips")
if not filtered_data.empty:
    recent_trips = filtered_data.sort_values('date', ascending=False).head(10)
    display_columns = ['date', 'customer', 'from_location', 'to_location', 'tons_loaded', 'plate_number', 'distance_km']
    available_columns = [col for col in display_columns if col in recent_trips.columns]
    st.dataframe(recent_trips[available_columns], use_container_width=True)
else:
    st.info("No trip data available to display")

# Performance summary
if not filtered_data.empty:
    st.subheader("Performance Summary")
    col1, col2, col3 = st.columns(3)

    with col1:
        if 'distance_km' in filtered_data.columns and 'tons_loaded' in filtered_data.columns:
            total_tkm = (filtered_data['distance_km'] * filtered_data['tons_loaded']).sum()
            st.metric("Total Ton-Kilometers", f"{total_tkm:,.0f} tkm")

    with col2:
        if not st.session_state.energy_consumption.empty:
            avg_efficiency = st.session_state.energy_consumption['kwh_per_km'].mean()
            st.metric("Average Efficiency", f"{avg_efficiency:.2f} kWh/km")

    with col3:
        if not st.session_state.energy_consumption.empty and 'distance_km' in filtered_data.columns:
            total_energy = 0
            for truck in filtered_data['plate_number'].unique():
                truck_km = filtered_data[filtered_data['plate_number'] == truck]['distance_km'].sum()
                truck_efficiency = st.session_state.energy_consumption[
                    st.session_state.energy_consumption['plate_number'] == truck
                ]['kwh_per_km'].mean()
                if not pd.isna(truck_efficiency):
                    total_energy += truck_km * truck_efficiency

            total_emissions = total_energy * st.session_state.emission_factor
            st.metric("Total CO2 Emissions", f"{total_emissions:,.0f} kg")