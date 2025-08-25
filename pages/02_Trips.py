import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

st.set_page_config(page_title="Trips", page_icon="🚛", layout="wide")

st.title("🚛 Trips Management")

# Display current trips data
st.subheader("Trip Data")

if st.session_state.trips_data.empty:
    st.info("No trip data available. Import data from the Data & Import section.")
else:
    # Search and filter options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        search_term = st.text_input("Search trips (customer, plate, location)")
    
    with col2:
        if 'plate_number' in st.session_state.trips_data.columns:
            plate_filter = st.selectbox(
                "Filter by Truck",
                ['All'] + list(st.session_state.trips_data['plate_number'].unique())
            )
        else:
            plate_filter = 'All'
    
    with col3:
        if 'customer' in st.session_state.trips_data.columns:
            customer_filter = st.selectbox(
                "Filter by Customer",
                ['All'] + list(st.session_state.trips_data['customer'].unique())
            )
        else:
            customer_filter = 'All'
    
    # Apply filters
    filtered_trips = st.session_state.trips_data.copy()
    
    if search_term:
        search_columns = ['customer', 'plate_number', 'from_location', 'to_location']
        available_search_columns = [col for col in search_columns if col in filtered_trips.columns]
        if available_search_columns:
            mask = filtered_trips[available_search_columns].astype(str).apply(
                lambda x: x.str.contains(search_term, case=False, na=False)
            ).any(axis=1)
            filtered_trips = filtered_trips[mask]
    
    if plate_filter != 'All':
        filtered_trips = filtered_trips[filtered_trips['plate_number'] == plate_filter]
    
    if customer_filter != 'All':
        filtered_trips = filtered_trips[filtered_trips['customer'] == customer_filter]
    
    # Display filtered data
    st.dataframe(filtered_trips, use_container_width=True, height=400)
    
    # Trip statistics
    st.subheader("Trip Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_trips = len(filtered_trips)
        st.metric("Total Trips", total_trips)
    
    with col2:
        if 'distance_km' in filtered_trips.columns:
            total_distance = filtered_trips['distance_km'].sum()
            st.metric("Total Distance", f"{total_distance:,.0f} km")
        else:
            st.metric("Total Distance", "N/A")
    
    with col3:
        if 'tons_loaded' in filtered_trips.columns:
            total_cargo = filtered_trips['tons_loaded'].sum()
            st.metric("Total Cargo", f"{total_cargo:,.0f} tons")
        else:
            st.metric("Total Cargo", "N/A")
    
    with col4:
        unique_customers = filtered_trips['customer'].nunique() if 'customer' in filtered_trips.columns else 0
        st.metric("Unique Customers", unique_customers)
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Trips by Customer")
        if 'customer' in filtered_trips.columns and not filtered_trips.empty:
            customer_counts = filtered_trips['customer'].value_counts().head(10)
            fig = px.pie(
                values=customer_counts.values,
                names=customer_counts.index,
                title="Top 10 Customers by Trip Count"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No customer data available")
    
    with col2:
        st.subheader("Daily Trip Volume")
        if 'date' in filtered_trips.columns and not filtered_trips.empty:
            try:
                filtered_trips['date'] = pd.to_datetime(filtered_trips['date'])
                daily_trips = filtered_trips.groupby(filtered_trips['date'].dt.date).size()
                fig = px.line(
                    x=daily_trips.index,
                    y=daily_trips.values,
                    title="Trips per Day",
                    labels={'x': 'Date', 'y': 'Number of Trips'}
                )
                st.plotly_chart(fig, use_container_width=True)
            except:
                st.error("Invalid date format in trip data")
        else:
            st.info("No date data available")

# Manual trip entry
st.subheader("Add New Trip")
with st.expander("Manual Trip Entry"):
    with st.form("add_trip"):
        col1, col2 = st.columns(2)
        
        with col1:
            trip_date = st.date_input("Trip Date", datetime.now().date())
            customer = st.text_input("Customer")
            from_location = st.text_input("From Location")
            to_location = st.text_input("To Location")
        
        with col2:
            tons_loaded = st.number_input("Tons Loaded", min_value=0.0, step=0.1)
            truck_type = st.text_input("Truck Type")
            plate_number = st.text_input("Plate Number")
            distance_km = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        
        submitted = st.form_submit_button("Add Trip")
        
        if submitted:
            new_trip = pd.DataFrame({
                'date': [trip_date],
                'customer': [customer],
                'from_location': [from_location],
                'to_location': [to_location],
                'tons_loaded': [tons_loaded],
                'truck_type': [truck_type],
                'plate_number': [plate_number],
                'distance_km': [distance_km]
            })
            
            st.session_state.trips_data = pd.concat([st.session_state.trips_data, new_trip], ignore_index=True)
            st.success("Trip added successfully!")
            st.rerun()

# Export filtered data
if not filtered_trips.empty:
    st.subheader("Export Data")
    csv = filtered_trips.to_csv(index=False)
    st.download_button(
        label="Download filtered trips as CSV",
        data=csv,
        file_name=f"trips_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
