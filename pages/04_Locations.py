import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import re

st.set_page_config(page_title="Locations", page_icon="📍", layout="wide")

st.markdown("""
<style>
    h1 { color: #002664 !important; }
    h2 { color: #002664 !important; }
    h3 { color: #002664 !important; }
    .stButton > button { background-color: #002664; color: white; }
    [data-testid="metric-container"] { background: white; border: 1px solid #e0e0e0; border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

st.title("📍 Location Management")

st.subheader("Manage Pickup and Delivery Locations")

# Display current locations
if st.session_state.locations_data.empty:
    st.info("No locations defined. Add locations using the form below or import from Excel.")
else:
    # Search functionality
    search_location = st.text_input("Search locations")
    
    display_locations = st.session_state.locations_data.copy()
    if search_location:
        mask = display_locations['location_name'].str.contains(search_location, case=False, na=False)
        display_locations = display_locations[mask]
    
    # Display locations table with edit functionality
    st.subheader("Current Locations")
    
    # Create editable dataframe
    edited_df = st.data_editor(
        display_locations,
        column_config={
            "location_name": st.column_config.TextColumn("Location Name", required=True),
            "coordinates": st.column_config.TextColumn("Coordinates (lat,lng)", required=True)
        },
        num_rows="dynamic",
        use_container_width=True
    )
    
    # Update session state if data was edited
    if not edited_df.equals(display_locations):
        # Validate coordinates format
        valid_data = []
        for idx, row in edited_df.iterrows():
            coord_pattern = r'^-?\d+\.?\d*,-?\d+\.?\d*$'
            if pd.notna(row['coordinates']) and re.match(coord_pattern, str(row['coordinates']).strip()):
                valid_data.append(row)
            elif pd.notna(row['location_name']) and row['location_name'].strip():
                st.error(f"Invalid coordinate format for {row['location_name']}. Use format: lat,lng (e.g., 40.7128,-74.0060)")
        
        if valid_data:
            st.session_state.locations_data = pd.DataFrame(valid_data)
            st.success("Locations updated successfully!")
            st.rerun()

# Add new location form
st.subheader("Add New Location")
with st.form("add_location"):
    col1, col2 = st.columns(2)
    
    with col1:
        location_name = st.text_input("Location Name", placeholder="e.g., Warehouse A")
    
    with col2:
        coordinates = st.text_input("Coordinates", placeholder="e.g., 40.7128,-74.0060")
    
    submitted = st.form_submit_button("Add Location")
    
    if submitted:
        if location_name and coordinates:
            # Validate coordinate format
            coord_pattern = r'^-?\d+\.?\d*,-?\d+\.?\d*$'
            if re.match(coord_pattern, coordinates.strip()):
                new_location = pd.DataFrame({
                    'location_name': [location_name],
                    'coordinates': [coordinates.strip()]
                })
                
                st.session_state.locations_data = pd.concat([
                    st.session_state.locations_data, 
                    new_location
                ], ignore_index=True)
                
                st.success(f"Location '{location_name}' added successfully!")
                st.rerun()
            else:
                st.error("Invalid coordinate format. Please use format: lat,lng (e.g., 40.7128,-74.0060)")
        else:
            st.error("Please fill in both location name and coordinates.")

# Map visualization
if not st.session_state.locations_data.empty:
    st.subheader("Location Map")
    
    # Create map
    # Calculate center of all locations
    try:
        coords_list = []
        for coord_str in st.session_state.locations_data['coordinates']:
            if pd.notna(coord_str):
                lat, lng = map(float, coord_str.split(','))
                coords_list.append([lat, lng])
        
        if coords_list:
            center_lat = sum(coord[0] for coord in coords_list) / len(coords_list)
            center_lng = sum(coord[1] for coord in coords_list) / len(coords_list)
            
            m = folium.Map(location=[center_lat, center_lng], zoom_start=10)
            
            # Add markers for each location
            for idx, row in st.session_state.locations_data.iterrows():
                if pd.notna(row['coordinates']):
                    try:
                        lat, lng = map(float, row['coordinates'].split(','))
                        folium.Marker(
                            [lat, lng],
                            popup=row['location_name'],
                            tooltip=row['location_name']
                        ).add_to(m)
                    except:
                        continue
            
            # Display map
            map_data = st_folium(m, width=700, height=500)
    
    except Exception as e:
        st.error(f"Error displaying map: {str(e)}")

# Import locations from Excel
st.subheader("Import Locations from Excel")
with st.expander("Upload Locations File"):
    uploaded_file = st.file_uploader(
        "Choose Excel file", 
        type=['xlsx', 'xls'],
        help="Excel file should have columns: location_name, coordinates"
    )
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            
            # Check required columns
            required_columns = ['location_name', 'coordinates']
            if all(col in df.columns for col in required_columns):
                # Validate coordinates
                valid_rows = []
                coord_pattern = r'^-?\d+\.?\d*,-?\d+\.?\d*$'
                
                for idx, row in df.iterrows():
                    if pd.notna(row['coordinates']) and re.match(coord_pattern, str(row['coordinates']).strip()):
                        valid_rows.append({
                            'location_name': row['location_name'],
                            'coordinates': str(row['coordinates']).strip()
                        })
                
                if valid_rows:
                    new_locations_df = pd.DataFrame(valid_rows)
                    
                    # Show preview
                    st.write("Preview of locations to be imported:")
                    st.dataframe(new_locations_df)
                    
                    if st.button("Import Locations"):
                        st.session_state.locations_data = pd.concat([
                            st.session_state.locations_data,
                            new_locations_df
                        ], ignore_index=True).drop_duplicates(subset=['location_name'], keep='last')
                        
                        st.success(f"Successfully imported {len(valid_rows)} locations!")
                        st.rerun()
                else:
                    st.error("No valid locations found in the file. Please check coordinate format.")
            else:
                st.error(f"Missing required columns. Expected: {required_columns}, Found: {list(df.columns)}")
        
        except Exception as e:
            st.error(f"Error reading Excel file: {str(e)}")

# Export locations
if not st.session_state.locations_data.empty:
    st.subheader("Export Locations")
    col1, col2 = st.columns(2)
    
    with col1:
        csv = st.session_state.locations_data.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name=f"locations_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Create Excel file in memory
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.locations_data.to_excel(writer, index=False, sheet_name='Locations')
        
        st.download_button(
            label="Download as Excel",
            data=output.getvalue(),
            file_name=f"locations_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# Location statistics
if not st.session_state.locations_data.empty:
    st.subheader("Location Statistics")
    col1, col2 = st.columns(2)
    
    with col1:
        total_locations = len(st.session_state.locations_data)
        st.metric("Total Locations", total_locations)
    
    with col2:
        # Count usage in trips
        if not st.session_state.trips_data.empty:
            used_locations = set()
            if 'from_location' in st.session_state.trips_data.columns:
                used_locations.update(st.session_state.trips_data['from_location'].dropna().unique())
            if 'to_location' in st.session_state.trips_data.columns:
                used_locations.update(st.session_state.trips_data['to_location'].dropna().unique())
            
            used_count = len(used_locations.intersection(set(st.session_state.locations_data['location_name'])))
            st.metric("Locations Used in Trips", used_count)
