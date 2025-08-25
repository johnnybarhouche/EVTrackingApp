import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
import plotly.express as px
from utils.calculations import calculate_emissions_report

st.set_page_config(page_title="Export", page_icon="📤", layout="wide")

st.title("📤 Export & Reports")

# Check if we have data
if st.session_state.trips_data.empty:
    st.warning("No trip data available. Please import data first.")
    st.stop()

# Date range selection
st.subheader("Select Reporting Period")
col1, col2 = st.columns(2)

with col1:
    # Get date range from trip data
    try:
        st.session_state.trips_data['date'] = pd.to_datetime(st.session_state.trips_data['date'])
        min_date = st.session_state.trips_data['date'].min().date()
        max_date = st.session_state.trips_data['date'].max().date()
        
        start_date = st.date_input(
            "Start Date",
            value=min_date,
            min_value=min_date,
            max_value=max_date
        )
    except:
        start_date = datetime.now().date() - timedelta(days=30)

with col2:
    try:
        end_date = st.date_input(
            "End Date", 
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    except:
        end_date = datetime.now().date()

# Filter data by date range
filtered_data = st.session_state.trips_data.copy()
try:
    filtered_data = filtered_data[
        (filtered_data['date'].dt.date >= start_date) & 
        (filtered_data['date'].dt.date <= end_date)
    ]
except:
    st.error("Error filtering data by date. Please check your trip data format.")

st.write(f"**Selected period:** {start_date} to {end_date}")
st.write(f"**Trips in period:** {len(filtered_data)}")

# Export options
st.header("Export Options")

# Tab layout for different export types
tab1, tab2, tab3 = st.tabs(["Monthly Emissions Report", "Customer Reports", "Raw Data Export"])

with tab1:
    st.subheader("📊 Monthly Emissions Report")
    
    if not filtered_data.empty:
        # Calculate emissions for the period
        emissions_data = calculate_emissions_report(
            filtered_data,
            st.session_state.energy_consumption,
            st.session_state.emission_factor
        )
        
        # Display summary
        st.subheader("Report Summary")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_trips = len(filtered_data)
            st.metric("Total Trips", total_trips)
        
        with col2:
            total_distance = filtered_data['distance_km'].sum()
            st.metric("Total Distance", f"{total_distance:,.0f} km")
        
        with col3:
            total_cargo = filtered_data['tons_loaded'].sum()
            st.metric("Total Cargo", f"{total_cargo:,.0f} tons")
        
        with col4:
            if not emissions_data.empty:
                total_emissions = emissions_data['total_co2_kg'].sum()
                st.metric("Total CO2 Emissions", f"{total_emissions:,.0f} kg")
        
        # Show detailed emissions data
        if not emissions_data.empty:
            st.subheader("Emissions by Truck")
            st.dataframe(emissions_data, use_container_width=True)
            
            # Create Excel report
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                # Summary sheet
                summary_data = pd.DataFrame({
                    'Metric': ['Total Trips', 'Total Distance (km)', 'Total Cargo (tons)', 'Total CO2 Emissions (kg)'],
                    'Value': [total_trips, total_distance, total_cargo, emissions_data['total_co2_kg'].sum()]
                })
                summary_data.to_excel(writer, sheet_name='Summary', index=False)
                
                # Detailed emissions
                emissions_data.to_excel(writer, sheet_name='Emissions by Truck', index=False)
                
                # Trip details
                export_trips = filtered_data.copy()
                # Add calculated emissions per trip
                trip_emissions = []
                for idx, trip in export_trips.iterrows():
                    truck_efficiency = 1.0  # Default
                    if not st.session_state.energy_consumption.empty:
                        truck_data = st.session_state.energy_consumption[
                            st.session_state.energy_consumption['plate_number'] == trip['plate_number']
                        ]
                        if not truck_data.empty:
                            truck_efficiency = truck_data['kwh_per_km'].mean()
                    
                    trip_kwh = trip['distance_km'] * truck_efficiency
                    trip_co2 = trip_kwh * st.session_state.emission_factor
                    trip_emissions.append(trip_co2)
                
                export_trips['trip_kwh'] = [trip['distance_km'] * 1.0 for idx, trip in export_trips.iterrows()]
                export_trips['trip_co2_kg'] = trip_emissions
                export_trips.to_excel(writer, sheet_name='Trip Details', index=False)
            
            st.download_button(
                label="📥 Download Monthly Emissions Report (Excel)",
                data=output.getvalue(),
                file_name=f"emissions_report_{start_date}_{end_date}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No emissions data available. Please ensure energy consumption data is imported.")
    
    else:
        st.info("No trip data available for the selected period.")

with tab2:
    st.subheader("👥 Customer Emissions Reports")
    
    if not filtered_data.empty and 'customer' in filtered_data.columns:
        # Customer selection
        customers = filtered_data['customer'].unique()
        selected_customer = st.selectbox("Select Customer", customers)
        
        if selected_customer:
            customer_data = filtered_data[filtered_data['customer'] == selected_customer]
            
            # Calculate customer-specific metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                customer_trips = len(customer_data)
                st.metric("Customer Trips", customer_trips)
            
            with col2:
                customer_distance = customer_data['distance_km'].sum()
                st.metric("Total Distance", f"{customer_distance:,.0f} km")
            
            with col3:
                customer_cargo = customer_data['tons_loaded'].sum()
                st.metric("Total Cargo", f"{customer_cargo:,.0f} tons")
            
            # Calculate emissions for this customer
            if not st.session_state.energy_consumption.empty:
                customer_emissions = 0
                for idx, trip in customer_data.iterrows():
                    truck_efficiency = st.session_state.energy_consumption[
                        st.session_state.energy_consumption['plate_number'] == trip['plate_number']
                    ]['kwh_per_km'].mean()
                    
                    if not pd.isna(truck_efficiency):
                        trip_kwh = trip['distance_km'] * truck_efficiency
                        trip_co2 = trip_kwh * st.session_state.emission_factor
                        customer_emissions += trip_co2
                
                st.metric("Total CO2 Emissions", f"{customer_emissions:,.0f} kg CO2")
                
                # Efficiency metrics
                if customer_cargo > 0:
                    co2_per_ton = customer_emissions / customer_cargo
                    st.metric("CO2 per Ton", f"{co2_per_ton:.2f} kg CO2/ton")
            
            # Customer trip details
            st.subheader("Trip Details")
            st.dataframe(customer_data, use_container_width=True)
            
            # Create customer report
            if st.button("Generate Customer Report"):
                # Create detailed customer report
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    # Customer summary
                    customer_summary = pd.DataFrame({
                        'Customer': [selected_customer],
                        'Period': [f"{start_date} to {end_date}"],
                        'Total Trips': [customer_trips],
                        'Total Distance (km)': [customer_distance],
                        'Total Cargo (tons)': [customer_cargo],
                        'CO2 Emissions (kg)': [customer_emissions if not st.session_state.energy_consumption.empty else 'N/A']
                    })
                    customer_summary.to_excel(writer, sheet_name='Customer Summary', index=False)
                    
                    # Trip details
                    customer_data.to_excel(writer, sheet_name='Trip Details', index=False)
                
                st.download_button(
                    label=f"📥 Download {selected_customer} Emissions Report",
                    data=output.getvalue(),
                    file_name=f"{selected_customer}_emissions_report_{start_date}_{end_date}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
    else:
        st.info("No customer data available for the selected period.")

with tab3:
    st.subheader("📋 Raw Data Export")
    
    # Data export options
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Trip Data Export**")
        if not filtered_data.empty:
            csv_trips = filtered_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Trip Data (CSV)",
                data=csv_trips,
                file_name=f"trip_data_{start_date}_{end_date}.csv",
                mime="text/csv"
            )
        
        st.write("**Energy Consumption Export**")
        if not st.session_state.energy_consumption.empty:
            csv_energy = st.session_state.energy_consumption.to_csv(index=False)
            st.download_button(
                label="📥 Download Energy Data (CSV)",
                data=csv_energy,
                file_name=f"energy_consumption_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col2:
        st.write("**Locations Export**")
        if not st.session_state.locations_data.empty:
            csv_locations = st.session_state.locations_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Locations (CSV)",
                data=csv_locations,
                file_name=f"locations_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        
        st.write("**Routes Export**")
        if not st.session_state.routes_data.empty:
            csv_routes = st.session_state.routes_data.to_csv(index=False)
            st.download_button(
                label="📥 Download Routes (CSV)",
                data=csv_routes,
                file_name=f"routes_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    # Complete data export
    st.write("**Complete Data Export (Excel)**")
    if st.button("Generate Complete Data Export"):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            if not filtered_data.empty:
                filtered_data.to_excel(writer, sheet_name='Trip Data', index=False)
            if not st.session_state.energy_consumption.empty:
                st.session_state.energy_consumption.to_excel(writer, sheet_name='Energy Consumption', index=False)
            if not st.session_state.locations_data.empty:
                st.session_state.locations_data.to_excel(writer, sheet_name='Locations', index=False)
            if not st.session_state.routes_data.empty:
                st.session_state.routes_data.to_excel(writer, sheet_name='Routes', index=False)
        
        st.download_button(
            label="📥 Download Complete Dataset (Excel)",
            data=output.getvalue(),
            file_name=f"complete_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Report preview
if not filtered_data.empty:
    st.header("📈 Report Preview")
    
    # Charts for the selected period
    col1, col2 = st.columns(2)
    
    with col1:
        # Trips by truck
        trips_by_truck = filtered_data['plate_number'].value_counts()
        fig_trips = px.bar(
            x=trips_by_truck.index,
            y=trips_by_truck.values,
            title="Trips by Truck",
            labels={'x': 'Truck', 'y': 'Number of Trips'}
        )
        st.plotly_chart(fig_trips, use_container_width=True)
    
    with col2:
        # Distance by truck
        distance_by_truck = filtered_data.groupby('plate_number')['distance_km'].sum()
        fig_distance = px.bar(
            x=distance_by_truck.index,
            y=distance_by_truck.values,
            title="Distance by Truck",
            labels={'x': 'Truck', 'y': 'Total Distance (km)'}
        )
        st.plotly_chart(fig_distance, use_container_width=True)
