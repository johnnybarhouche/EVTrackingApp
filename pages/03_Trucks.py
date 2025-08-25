import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.calculations import calculate_truck_metrics

st.set_page_config(page_title="Trucks", page_icon="🚚", layout="wide")

st.markdown("""
<style>
    h1 { color: #002664 !important; }
    h2 { color: #002664 !important; }
    h3 { color: #002664 !important; }
    .stButton > button { background-color: #002664; color: white; }
    [data-testid="metric-container"] { background: white; border: 1px solid #e0e0e0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("🚚 Truck Fleet Management")

# Calculate truck metrics if we have data
if not st.session_state.trips_data.empty:
    truck_metrics = calculate_truck_metrics(
        st.session_state.trips_data,
        st.session_state.energy_consumption,
        st.session_state.emission_factor
    )
    
    # Update trucks_data in session state
    st.session_state.trucks_data = truck_metrics
    
    st.subheader("Fleet Performance Overview")
    
    # Display metrics table
    if not truck_metrics.empty:
        # Format the dataframe for better display
        display_df = truck_metrics.copy()
        
        # Round numerical columns
        numerical_cols = ['total_km', 'total_kwh', 'kwh_per_km', 'total_tkm', 
                         'kg_co2', 'kwh_per_tkm', 'kg_co2_per_tkm', 'kg_co2_per_km']
        for col in numerical_cols:
            if col in display_df.columns:
                display_df[col] = display_df[col].round(2)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Fleet summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_fleet_km = display_df['total_km'].sum()
            st.metric("Total Fleet Distance", f"{total_fleet_km:,.0f} km")
        
        with col2:
            total_fleet_kwh = display_df['total_kwh'].sum()
            st.metric("Total Energy Consumed", f"{total_fleet_kwh:,.0f} kWh")
        
        with col3:
            avg_efficiency = display_df['kwh_per_km'].mean()
            st.metric("Average Fleet Efficiency", f"{avg_efficiency:.2f} kWh/km")
        
        with col4:
            total_emissions = display_df['kg_co2'].sum()
            st.metric("Total Fleet Emissions", f"{total_emissions:,.0f} kg CO2")
        
        # Visualization section
        st.subheader("Fleet Performance Visualizations")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Energy efficiency comparison
            fig_efficiency = px.bar(
                display_df,
                x='plate',
                y='kwh_per_km',
                title="Energy Efficiency by Truck (kWh/km)",
                color='kwh_per_km',
                color_continuous_scale='RdYlGn_r'
            )
            fig_efficiency.update_layout(showlegend=False)
            st.plotly_chart(fig_efficiency, use_container_width=True)
        
        with col2:
            # CO2 emissions comparison
            fig_emissions = px.bar(
                display_df,
                x='plate',
                y='kg_co2_per_km',
                title="CO2 Emissions by Truck (kg CO2/km)",
                color='kg_co2_per_km',
                color_continuous_scale='Reds'
            )
            fig_emissions.update_layout(showlegend=False)
            st.plotly_chart(fig_emissions, use_container_width=True)
        
        # Performance scatter plot
        st.subheader("Performance Analysis")
        
        fig_scatter = px.scatter(
            display_df,
            x='total_km',
            y='kwh_per_km',
            size='total_trips',
            color='kg_co2_per_km',
            hover_data=['plate', 'make'],
            title="Distance vs Efficiency (bubble size = number of trips)",
            labels={
                'total_km': 'Total Distance (km)',
                'kwh_per_km': 'Energy Efficiency (kWh/km)',
                'kg_co2_per_km': 'CO2 Emissions (kg/km)'
            }
        )
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Individual truck analysis
        st.subheader("Individual Truck Analysis")
        
        selected_truck = st.selectbox(
            "Select truck for detailed analysis:",
            display_df['plate'].tolist()
        )
        
        if selected_truck:
            truck_data = display_df[display_df['plate'] == selected_truck].iloc[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Trips", int(truck_data['total_trips']))
                st.metric("Total Distance", f"{truck_data['total_km']:,.0f} km")
                st.metric("Total Cargo", f"{truck_data['total_tkm']:,.0f} tkm")
            
            with col2:
                st.metric("Energy Efficiency", f"{truck_data['kwh_per_km']:.2f} kWh/km")
                st.metric("Cargo Efficiency", f"{truck_data['kwh_per_tkm']:.2f} kWh/tkm")
                st.metric("Total Energy", f"{truck_data['total_kwh']:,.0f} kWh")
            
            with col3:
                st.metric("CO2 per km", f"{truck_data['kg_co2_per_km']:.2f} kg")
                st.metric("CO2 per tkm", f"{truck_data['kg_co2_per_tkm']:.2f} kg")
                st.metric("Total CO2", f"{truck_data['kg_co2']:,.0f} kg")
            
            # Trip history for selected truck
            truck_trips = st.session_state.trips_data[
                st.session_state.trips_data['plate_number'] == selected_truck
            ].copy()
            
            if not truck_trips.empty:
                st.subheader(f"Trip History - {selected_truck}")
                st.dataframe(truck_trips, use_container_width=True)
    
    else:
        st.warning("No truck performance data available. Please ensure you have imported both trip data and energy consumption data.")

else:
    st.warning("No trip data available. Please import trip data from the Data & Import section.")

# Fleet Master Data
st.subheader("Fleet Master Data")
if 'truck_master_data' in st.session_state:
    st.dataframe(st.session_state.truck_master_data, use_container_width=True)
else:
    st.info("No truck master data available")

# Export truck data
if not st.session_state.trucks_data.empty:
    st.subheader("Export Fleet Data")
    csv = st.session_state.trucks_data.to_csv(index=False)
    st.download_button(
        label="Download fleet performance data as CSV",
        data=csv,
        file_name=f"fleet_performance_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
