import pandas as pd
import numpy as np
from datetime import datetime

def clean_trip_data(df):
    """
    Clean and validate trip data
    """
    cleaned_df = df.copy()
    
    # Convert date column to datetime
    try:
        cleaned_df['date'] = pd.to_datetime(cleaned_df['date'])
    except:
        pass
    
    # Remove rows with missing essential data
    essential_columns = ['date', 'customer', 'from_location', 'to_location', 'plate_number']
    available_essential = [col for col in essential_columns if col in cleaned_df.columns]
    cleaned_df = cleaned_df.dropna(subset=available_essential)
    
    # Clean numeric columns
    numeric_columns = ['tons_loaded', 'distance_km']
    for col in numeric_columns:
        if col in cleaned_df.columns:
            # Convert to numeric, replacing non-numeric values with 0
            cleaned_df[col] = pd.to_numeric(cleaned_df[col], errors='coerce').fillna(0)
            # Remove negative values
            cleaned_df[col] = cleaned_df[col].clip(lower=0)
    
    # Clean text columns
    text_columns = ['customer', 'from_location', 'to_location', 'truck_type', 'plate_number']
    for col in text_columns:
        if col in cleaned_df.columns:
            cleaned_df[col] = cleaned_df[col].astype(str).str.strip()
    
    return cleaned_df

def clean_energy_data(df):
    """
    Clean and validate energy consumption data
    """
    cleaned_df = df.copy()
    
    # Clean plate numbers
    if 'plate_number' in cleaned_df.columns:
        cleaned_df['plate_number'] = cleaned_df['plate_number'].astype(str).str.strip()
    
    # Validate and clean kWh/km values
    if 'kwh_per_km' in cleaned_df.columns:
        cleaned_df['kwh_per_km'] = pd.to_numeric(cleaned_df['kwh_per_km'], errors='coerce')
        # Remove unrealistic values (negative or extremely high)
        cleaned_df = cleaned_df[
            (cleaned_df['kwh_per_km'] >= 0.1) & 
            (cleaned_df['kwh_per_km'] <= 10.0)
        ]
    
    # Clean period format
    if 'period' in cleaned_df.columns:
        cleaned_df['period'] = cleaned_df['period'].astype(str).str.strip()
    
    return cleaned_df.dropna()

def merge_trip_energy_data(trips_df, energy_df):
    """
    Merge trip data with energy consumption data
    """
    if trips_df.empty or energy_df.empty:
        return trips_df
    
    # Get the most recent energy data for each truck
    latest_energy = energy_df.groupby('plate_number').agg({
        'kwh_per_km': 'mean',  # Average efficiency for the truck
        'period': 'max'        # Most recent period
    }).reset_index()
    
    # Merge with trip data
    merged_df = trips_df.merge(
        latest_energy,
        left_on='plate_number',
        right_on='plate_number',
        how='left'
    )
    
    return merged_df

def calculate_trip_distances(trips_df, routes_df):
    """
    Calculate distances for trips using routes data
    """
    if trips_df.empty or routes_df.empty:
        return trips_df
    
    updated_trips = trips_df.copy()
    
    # Create a route lookup dictionary
    route_lookup = {}
    for idx, route in routes_df.iterrows():
        key = (route['from_location_name'], route['to_location_name'])
        route_lookup[key] = route['km_distance']
    
    # Update distances where missing or zero
    for idx, trip in updated_trips.iterrows():
        if pd.isna(trip.get('distance_km', 0)) or trip.get('distance_km', 0) == 0:
            route_key = (trip['from_location'], trip['to_location'])
            if route_key in route_lookup:
                updated_trips.loc[idx, 'distance_km'] = route_lookup[route_key]
    
    return updated_trips

def aggregate_truck_performance(trips_df, energy_df, emission_factor=0.5):
    """
    Aggregate performance metrics by truck
    """
    if trips_df.empty:
        return pd.DataFrame()
    
    # Aggregate trip data by truck
    truck_aggregates = trips_df.groupby('plate_number').agg({
        'date': 'count',  # Total trips
        'distance_km': 'sum',  # Total distance
        'tons_loaded': 'sum'   # Total cargo
    }).rename(columns={'date': 'total_trips'})
    
    # Calculate ton-kilometers
    if 'distance_km' in trips_df.columns and 'tons_loaded' in trips_df.columns:
        truck_aggregates['total_tkm'] = (
            trips_df.groupby('plate_number')
            .apply(lambda x: (x['distance_km'] * x['tons_loaded']).sum())
        )
    else:
        truck_aggregates['total_tkm'] = 0
    
    # Add energy efficiency data
    if not energy_df.empty:
        avg_efficiency = energy_df.groupby('plate_number')['kwh_per_km'].mean()
        truck_aggregates = truck_aggregates.join(avg_efficiency, how='left')
        
        # Calculate total energy consumption
        truck_aggregates['total_kwh'] = (
            truck_aggregates['distance_km'] * truck_aggregates['kwh_per_km']
        ).fillna(0)
        
        # Calculate emissions
        truck_aggregates['kg_co2'] = truck_aggregates['total_kwh'] * emission_factor
        
        # Calculate efficiency metrics
        truck_aggregates['kwh_per_tkm'] = np.where(
            truck_aggregates['total_tkm'] > 0,
            truck_aggregates['total_kwh'] / truck_aggregates['total_tkm'],
            0
        )
        
        truck_aggregates['kg_co2_per_tkm'] = np.where(
            truck_aggregates['total_tkm'] > 0,
            truck_aggregates['kg_co2'] / truck_aggregates['total_tkm'],
            0
        )
        
        truck_aggregates['kg_co2_per_km'] = np.where(
            truck_aggregates['distance_km'] > 0,
            truck_aggregates['kg_co2'] / truck_aggregates['distance_km'],
            0
        )
    else:
        # Set default values when no energy data is available
        for col in ['kwh_per_km', 'total_kwh', 'kg_co2', 'kwh_per_tkm', 'kg_co2_per_tkm', 'kg_co2_per_km']:
            truck_aggregates[col] = 0
    
    # Reset index to make plate_number a column
    truck_aggregates = truck_aggregates.reset_index()
    
    # Add make column (placeholder for now)
    truck_aggregates['make'] = 'Electric Truck'
    
    # Reorder columns
    column_order = [
        'plate_number', 'make', 'total_trips', 'distance_km', 'kwh_per_km',
        'total_kwh', 'total_tkm', 'kg_co2', 'kwh_per_tkm', 
        'kg_co2_per_tkm', 'kg_co2_per_km'
    ]
    
    # Rename columns to match expected format
    truck_aggregates = truck_aggregates.rename(columns={
        'plate_number': 'plate',
        'distance_km': 'total_km'
    })
    
    # Ensure all expected columns exist
    for col in column_order:
        col_name = col if col != 'plate_number' else 'plate'
        col_name = col_name if col_name != 'distance_km' else 'total_km'
        if col_name not in truck_aggregates.columns:
            truck_aggregates[col_name] = 0
    
    return truck_aggregates

def validate_coordinates(coord_string):
    """
    Validate coordinate string format (lat,lng)
    """
    try:
        parts = coord_string.split(',')
        if len(parts) != 2:
            return False
        
        lat, lng = float(parts[0].strip()), float(parts[1].strip())
        
        # Check if coordinates are within valid ranges
        if -90 <= lat <= 90 and -180 <= lng <= 180:
            return True
        return False
    except:
        return False

def format_coordinates(coord_string):
    """
    Format coordinate string to standard format
    """
    try:
        parts = coord_string.split(',')
        lat, lng = float(parts[0].strip()), float(parts[1].strip())
        return f"{lat:.6f},{lng:.6f}"
    except:
        return coord_string
