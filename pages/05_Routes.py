import streamlit as st
import pandas as pd
import plotly.express as px
from utils.google_maps import calculate_distance_google_maps
import numpy as np

st.set_page_config(page_title="Routes", page_icon="🛣️", layout="wide")

st.title("🛣️ Route Management")

st.subheader("Manage Routes and Distances")

# Display current routes
if st.session_state.routes_data.empty:
    st.info("No routes defined. Add routes using the form below or calculate from Google Maps.")
else:
    # Search functionality
    search_route = st.text_input("Search routes (from or to location)")
    
    display_routes = st.session_state.routes_data.copy()
    if search_route:
        mask = (display_routes['from_location_name'].str.contains(search_route, case=False, na=False) |
                display_routes['to_location_name'].str.contains(search_route, case=False, na=False))
        display_routes = display_routes[mask]
    
    # Display routes table with edit functionality
    st.subheader("Current Routes")
    
    edited_df = st.data_editor(
        display_routes,
        column_config={
            "from_location_name": st.column_config.TextColumn("From Location", required=True),
            "to_location_name": st.column_config.TextColumn("To Location", required=True),
            "km_distance": st.column_config.NumberColumn("Distance (km)", min_value=0.0, step=0.1),
            "source": st.column_config.TextColumn("Source")
        },
        num_rows="dynamic",
        use_container_width=True
    )
    
    # Update session state if data was edited
    if not edited_df.equals(display_routes):
        st.session_state.routes_data = edited_df.copy()
        st.success("Routes updated successfully!")
        st.rerun()

# Add new route form
st.subheader("Add New Route")
with st.form("add_route"):
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Get available locations for dropdowns
        available_locations = []
        if not st.session_state.locations_data.empty:
            available_locations = st.session_state.locations_data['location_name'].tolist()
        
        if available_locations:
            from_location = st.selectbox("From Location", [''] + available_locations)
            to_location = st.selectbox("To Location", [''] + available_locations)
        else:
            from_location = st.text_input("From Location")
            to_location = st.text_input("To Location")
    
    with col2:
        km_distance = st.number_input("Distance (km)", min_value=0.0, step=0.1)
        source = st.selectbox("Source", ["Manual", "Google Maps", "Other"])
    
    with col3:
        st.write("") # Spacing
        calculate_google = st.checkbox("Calculate distance using Google Maps")
    
    submitted = st.form_submit_button("Add Route")
    
    if submitted:
        if from_location and to_location:
            calculated_distance = km_distance
            route_source = source
            
            # Calculate distance using Google Maps if requested
            if calculate_google and not st.session_state.locations_data.empty:
                from_coords = None
                to_coords = None
                
                # Get coordinates for locations
                for idx, row in st.session_state.locations_data.iterrows():
                    if row['location_name'] == from_location:
                        from_coords = row['coordinates']
                    elif row['location_name'] == to_location:
                        to_coords = row['coordinates']
                
                if from_coords and to_coords:
                    with st.spinner("Calculating distance using Google Maps..."):
                        google_distance = calculate_distance_google_maps(from_coords, to_coords)
                        if google_distance:
                            calculated_distance = google_distance
                            route_source = "Google Maps"
                            st.success(f"Distance calculated: {google_distance:.1f} km")
                        else:
                            st.warning("Could not calculate distance using Google Maps. Using manual value.")
                else:
                    st.warning("Coordinates not found for one or both locations. Using manual distance.")
            
            new_route = pd.DataFrame({
                'from_location_name': [from_location],
                'to_location_name': [to_location],
                'km_distance': [calculated_distance],
                'source': [route_source]
            })
            
            st.session_state.routes_data = pd.concat([
                st.session_state.routes_data, 
                new_route
            ], ignore_index=True)
            
            st.success(f"Route from '{from_location}' to '{to_location}' added successfully!")
            st.rerun()
        else:
            st.error("Please fill in both from and to locations.")

# Bulk calculate distances
if not st.session_state.locations_data.empty:
    st.subheader("Bulk Distance Calculation")
    with st.expander("Calculate Missing Distances"):
        st.write("This will calculate distances for routes that are missing distance data using Google Maps.")
        
        # Find routes with missing distances
        missing_distances = st.session_state.routes_data[
            (st.session_state.routes_data['km_distance'].isna()) | 
            (st.session_state.routes_data['km_distance'] == 0)
        ]
        
        if not missing_distances.empty:
            st.write(f"Found {len(missing_distances)} routes with missing distances:")
            st.dataframe(missing_distances[['from_location_name', 'to_location_name']])
            
            if st.button("Calculate All Missing Distances"):
                with st.spinner("Calculating distances..."):
                    progress_bar = st.progress(0)
                    total_routes = len(missing_distances)
                    
                    for idx, (route_idx, route) in enumerate(missing_distances.iterrows()):
                        # Get coordinates
                        from_coords = None
                        to_coords = None
                        
                        for loc_idx, loc_row in st.session_state.locations_data.iterrows():
                            if loc_row['location_name'] == route['from_location_name']:
                                from_coords = loc_row['coordinates']
                            elif loc_row['location_name'] == route['to_location_name']:
                                to_coords = loc_row['coordinates']
                        
                        if from_coords and to_coords:
                            distance = calculate_distance_google_maps(from_coords, to_coords)
                            if distance:
                                st.session_state.routes_data.loc[route_idx, 'km_distance'] = distance
                                st.session_state.routes_data.loc[route_idx, 'source'] = 'Google Maps'
                        
                        progress_bar.progress((idx + 1) / total_routes)
                    
                    st.success("Distance calculation completed!")
                    st.rerun()
        else:
            st.info("No routes with missing distances found.")

# Auto-generate routes from trips
if not st.session_state.trips_data.empty:
    st.subheader("Auto-Generate Routes from Trips")
    with st.expander("Generate Routes from Trip Data"):
        st.write("This will create routes based on the from/to locations in your trip data.")
        
        # Find unique route combinations in trip data
        if 'from_location' in st.session_state.trips_data.columns and 'to_location' in st.session_state.trips_data.columns:
            trip_routes = st.session_state.trips_data[['from_location', 'to_location']].dropna().drop_duplicates()
            
            # Check which routes don't exist yet
            existing_routes = set()
            for idx, row in st.session_state.routes_data.iterrows():
                existing_routes.add((row['from_location_name'], row['to_location_name']))
            
            new_routes = []
            for idx, row in trip_routes.iterrows():
                if (row['from_location'], row['to_location']) not in existing_routes:
                    new_routes.append((row['from_location'], row['to_location']))
            
            if new_routes:
                st.write(f"Found {len(new_routes)} new routes from trip data:")
                new_routes_df = pd.DataFrame(new_routes, columns=['From', 'To'])
                st.dataframe(new_routes_df)
                
                if st.button("Generate Routes"):
                    with st.spinner("Generating routes..."):
                        for from_loc, to_loc in new_routes:
                            # Try to calculate distance
                            distance = 0
                            source = "Manual"
                            
                            # Get coordinates if available
                            from_coords = None
                            to_coords = None
                            
                            if not st.session_state.locations_data.empty:
                                for loc_idx, loc_row in st.session_state.locations_data.iterrows():
                                    if loc_row['location_name'] == from_loc:
                                        from_coords = loc_row['coordinates']
                                    elif loc_row['location_name'] == to_loc:
                                        to_coords = loc_row['coordinates']
                                
                                if from_coords and to_coords:
                                    calculated_distance = calculate_distance_google_maps(from_coords, to_coords)
                                    if calculated_distance:
                                        distance = calculated_distance
                                        source = "Google Maps"
                            
                            new_route = pd.DataFrame({
                                'from_location_name': [from_loc],
                                'to_location_name': [to_loc],
                                'km_distance': [distance],
                                'source': [source]
                            })
                            
                            st.session_state.routes_data = pd.concat([
                                st.session_state.routes_data,
                                new_route
                            ], ignore_index=True)
                    
                    st.success(f"Generated {len(new_routes)} new routes!")
                    st.rerun()
            else:
                st.info("All routes from trip data already exist.")

# Route statistics and visualizations
if not st.session_state.routes_data.empty:
    st.subheader("Route Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_routes = len(st.session_state.routes_data)
        st.metric("Total Routes", total_routes)
    
    with col2:
        avg_distance = st.session_state.routes_data['km_distance'].mean()
        st.metric("Average Distance", f"{avg_distance:.1f} km")
    
    with col3:
        google_routes = len(st.session_state.routes_data[st.session_state.routes_data['source'] == 'Google Maps'])
        st.metric("Google Maps Routes", google_routes)
    
    # Distance distribution chart
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Distance Distribution")
        fig_hist = px.histogram(
            st.session_state.routes_data,
            x='km_distance',
            title="Route Distance Distribution",
            labels={'km_distance': 'Distance (km)', 'count': 'Number of Routes'}
        )
        st.plotly_chart(fig_hist, use_container_width=True)
    
    with col2:
        st.subheader("Routes by Source")
        source_counts = st.session_state.routes_data['source'].value_counts()
        fig_pie = px.pie(
            values=source_counts.values,
            names=source_counts.index,
            title="Routes by Data Source"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# Export routes
if not st.session_state.routes_data.empty:
    st.subheader("Export Routes")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = st.session_state.routes_data.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"routes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.routes_data.to_excel(writer, index=False, sheet_name='Routes')
        
        st.download_button(
            label="Download as Excel",
            data=output.getvalue(),
            file_name=f"routes_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
