import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

def calculate_truck_metrics(trips_data: pd.DataFrame, energy_data: pd.DataFrame, emission_factor: float = 0.5) -> pd.DataFrame:
    """
    Calculate comprehensive truck performance metrics
    
    Args:
        trips_data: DataFrame containing trip information
        energy_data: DataFrame containing energy consumption data
        emission_factor: CO2 emission factor in kg CO2/kWh
    
    Returns:
        DataFrame with truck performance metrics
    """
    if trips_data.empty:
        return pd.DataFrame()
    
    # Aggregate basic trip metrics by truck
    truck_stats = trips_data.groupby('plate_number').agg({
        'date': 'count',  # Total trips
        'distance_km': 'sum',  # Total distance
        'tons_loaded': 'sum',  # Total cargo transported
    }).rename(columns={'date': 'total_trips'})
    
    # Calculate ton-kilometers (freight work done)
    truck_stats['total_tkm'] = (
        trips_data.groupby('plate_number')
        .apply(lambda x: (x['distance_km'] * x['tons_loaded']).sum(), include_groups=False)
    )
    
    # Add energy efficiency data if available
    if not energy_data.empty:
        # Get average efficiency per truck
        avg_efficiency = energy_data.groupby('plate_number')['kwh_per_km'].mean()
        truck_stats = truck_stats.join(avg_efficiency, how='left')
        
        # Fill missing efficiency values with fleet average
        fleet_avg_efficiency = avg_efficiency.mean()
        truck_stats['kwh_per_km'] = truck_stats['kwh_per_km'].fillna(fleet_avg_efficiency)
        
        # Calculate total energy consumption
        truck_stats['total_kwh'] = truck_stats['distance_km'] * truck_stats['kwh_per_km']
        
        # Calculate CO2 emissions
        truck_stats['kg_co2'] = truck_stats['total_kwh'] * emission_factor
        
        # Calculate efficiency metrics per ton-kilometer
        truck_stats['kwh_per_tkm'] = np.where(
            truck_stats['total_tkm'] > 0,
            truck_stats['total_kwh'] / truck_stats['total_tkm'],
            0
        )
        
        truck_stats['kg_co2_per_tkm'] = np.where(
            truck_stats['total_tkm'] > 0,
            truck_stats['kg_co2'] / truck_stats['total_tkm'],
            0
        )
        
        truck_stats['kg_co2_per_km'] = np.where(
            truck_stats['distance_km'] > 0,
            truck_stats['kg_co2'] / truck_stats['distance_km'],
            0
        )
    else:
        # Set default values when no energy data is available
        for col in ['kwh_per_km', 'total_kwh', 'kg_co2', 'kwh_per_tkm', 'kg_co2_per_tkm', 'kg_co2_per_km']:
            truck_stats[col] = 0.0
    
    # Reset index and rename columns to match expected format
    truck_stats = truck_stats.reset_index()
    truck_stats = truck_stats.rename(columns={
        'plate_number': 'plate',
        'distance_km': 'total_km'
    })
    
    # Add make column (can be enhanced with actual truck make data)
    truck_stats['make'] = 'Electric Truck'
    
    # Reorder columns to match expected output
    column_order = [
        'plate', 'make', 'total_trips', 'total_km', 'kwh_per_km',
        'total_kwh', 'total_tkm', 'kg_co2', 'kwh_per_tkm',
        'kg_co2_per_tkm', 'kg_co2_per_km'
    ]
    
    return truck_stats[column_order]

def calculate_emissions_report(trips_data: pd.DataFrame, energy_data: pd.DataFrame, emission_factor: float = 0.5) -> pd.DataFrame:
    """
    Calculate emissions report for all trucks in the given period
    
    Args:
        trips_data: Filtered trip data for the reporting period
        energy_data: Energy consumption data
        emission_factor: CO2 emission factor in kg CO2/kWh
    
    Returns:
        DataFrame with emissions data by truck
    """
    if trips_data.empty:
        return pd.DataFrame()
    
    # Get truck metrics
    truck_metrics = calculate_truck_metrics(trips_data, energy_data, emission_factor)
    
    if truck_metrics.empty:
        return pd.DataFrame()
    
    # Select relevant columns for emissions report
    emissions_columns = [
        'plate', 'total_trips', 'total_km', 'total_tkm',
        'total_kwh', 'kg_co2', 'kwh_per_km', 'kg_co2_per_km', 'kg_co2_per_tkm'
    ]
    
    emissions_report = truck_metrics[emissions_columns].copy()
    
    # Rename columns for better readability in reports
    emissions_report = emissions_report.rename(columns={
        'plate': 'truck_plate',
        'total_trips': 'trips_count',
        'total_km': 'distance_km',
        'total_tkm': 'ton_kilometers',
        'total_kwh': 'energy_consumed_kwh',
        'kg_co2': 'total_co2_kg',
        'kwh_per_km': 'energy_efficiency_kwh_km',
        'kg_co2_per_km': 'emissions_per_km',
        'kg_co2_per_tkm': 'emissions_per_tkm'
    })
    
    return emissions_report

def calculate_customer_emissions(trips_data: pd.DataFrame, energy_data: pd.DataFrame, 
                               customer_name: str, emission_factor: float = 0.5) -> Dict:
    """
    Calculate emissions for a specific customer
    
    Args:
        trips_data: Trip data filtered for the reporting period
        energy_data: Energy consumption data
        customer_name: Name of the customer
        emission_factor: CO2 emission factor in kg CO2/kWh
    
    Returns:
        Dictionary with customer emissions summary
    """
    if trips_data.empty or 'customer' not in trips_data.columns:
        return {}
    
    # Filter trips for the specific customer
    customer_trips = trips_data[trips_data['customer'] == customer_name].copy()
    
    if customer_trips.empty:
        return {
            'customer_name': customer_name,
            'total_trips': 0,
            'total_distance_km': 0,
            'total_cargo_tons': 0,
            'total_tkm': 0,
            'total_emissions_kg': 0,
            'emissions_per_ton': 0,
            'emissions_per_km': 0
        }
    
    # Calculate basic metrics
    total_trips = len(customer_trips)
    total_distance = customer_trips['distance_km'].sum()
    total_cargo = customer_trips['tons_loaded'].sum()
    total_tkm = (customer_trips['distance_km'] * customer_trips['tons_loaded']).sum()
    
    # Calculate emissions
    total_emissions = 0
    if not energy_data.empty:
        for _, trip in customer_trips.iterrows():
            # Get truck efficiency
            truck_efficiency_data = energy_data[
                energy_data['plate_number'] == trip['plate_number']
            ]
            
            if not truck_efficiency_data.empty:
                efficiency = truck_efficiency_data['kwh_per_km'].mean()
                trip_kwh = trip['distance_km'] * efficiency
                trip_co2 = trip_kwh * emission_factor
                total_emissions += trip_co2
    
    # Calculate efficiency metrics
    emissions_per_ton = total_emissions / total_cargo if total_cargo > 0 else 0
    emissions_per_km = total_emissions / total_distance if total_distance > 0 else 0
    
    return {
        'customer_name': customer_name,
        'total_trips': total_trips,
        'total_distance_km': round(total_distance, 2),
        'total_cargo_tons': round(total_cargo, 2),
        'total_tkm': round(total_tkm, 2),
        'total_emissions_kg': round(total_emissions, 2),
        'emissions_per_ton': round(emissions_per_ton, 2),
        'emissions_per_km': round(emissions_per_km, 2)
    }

def calculate_fleet_kpis(trips_data: pd.DataFrame, energy_data: pd.DataFrame, 
                        emission_factor: float = 0.5) -> Dict:
    """
    Calculate key performance indicators for the entire fleet
    
    Args:
        trips_data: Trip data
        energy_data: Energy consumption data
        emission_factor: CO2 emission factor in kg CO2/kWh
    
    Returns:
        Dictionary with fleet KPIs
    """
    if trips_data.empty:
        return {}
    
    # Basic fleet metrics
    total_trips = len(trips_data)
    total_distance = trips_data['distance_km'].sum()
    total_cargo = trips_data['tons_loaded'].sum()
    total_tkm = (trips_data['distance_km'] * trips_data['tons_loaded']).sum()
    active_trucks = trips_data['plate_number'].nunique()
    unique_customers = trips_data['customer'].nunique() if 'customer' in trips_data.columns else 0
    
    # Calculate fleet efficiency metrics
    avg_load_per_trip = total_cargo / total_trips if total_trips > 0 else 0
    avg_distance_per_trip = total_distance / total_trips if total_trips > 0 else 0
    utilization_tkm_per_truck = total_tkm / active_trucks if active_trucks > 0 else 0
    
    # Calculate energy and emissions metrics
    total_emissions = 0
    total_energy = 0
    fleet_avg_efficiency = 0
    
    if not energy_data.empty:
        truck_metrics = calculate_truck_metrics(trips_data, energy_data, emission_factor)
        if not truck_metrics.empty:
            total_energy = truck_metrics['total_kwh'].sum()
            total_emissions = truck_metrics['kg_co2'].sum()
            fleet_avg_efficiency = truck_metrics['kwh_per_km'].mean()
    
    # Efficiency ratios
    energy_per_tkm = total_energy / total_tkm if total_tkm > 0 else 0
    emissions_per_tkm = total_emissions / total_tkm if total_tkm > 0 else 0
    emissions_per_ton = total_emissions / total_cargo if total_cargo > 0 else 0
    
    return {
        'total_trips': total_trips,
        'total_distance_km': round(total_distance, 2),
        'total_cargo_tons': round(total_cargo, 2),
        'total_tkm': round(total_tkm, 2),
        'active_trucks': active_trucks,
        'unique_customers': unique_customers,
        'avg_load_per_trip': round(avg_load_per_trip, 2),
        'avg_distance_per_trip': round(avg_distance_per_trip, 2),
        'utilization_tkm_per_truck': round(utilization_tkm_per_truck, 2),
        'total_energy_kwh': round(total_energy, 2),
        'total_emissions_kg': round(total_emissions, 2),
        'fleet_avg_efficiency_kwh_km': round(fleet_avg_efficiency, 3),
        'energy_per_tkm': round(energy_per_tkm, 3),
        'emissions_per_tkm': round(emissions_per_tkm, 3),
        'emissions_per_ton': round(emissions_per_ton, 3)
    }

def calculate_monthly_summary(trips_data: pd.DataFrame, energy_data: pd.DataFrame,
                            emission_factor: float = 0.5) -> pd.DataFrame:
    """
    Calculate monthly performance summary
    
    Args:
        trips_data: Trip data with date column
        energy_data: Energy consumption data
        emission_factor: CO2 emission factor in kg CO2/kWh
    
    Returns:
        DataFrame with monthly summaries
    """
    if trips_data.empty or 'date' not in trips_data.columns:
        return pd.DataFrame()
    
    # Ensure date column is datetime
    trips_data = trips_data.copy()
    trips_data['date'] = pd.to_datetime(trips_data['date'])
    trips_data['year_month'] = trips_data['date'].dt.to_period('M')
    
    # Group by month and calculate metrics
    monthly_metrics = []
    
    for period, month_data in trips_data.groupby('year_month'):
        fleet_kpis = calculate_fleet_kpis(month_data, energy_data, emission_factor)
        
        monthly_summary = {
            'year_month': str(period),
            'trips_count': fleet_kpis.get('total_trips', 0),
            'distance_km': fleet_kpis.get('total_distance_km', 0),
            'cargo_tons': fleet_kpis.get('total_cargo_tons', 0),
            'tkm': fleet_kpis.get('total_tkm', 0),
            'active_trucks': fleet_kpis.get('active_trucks', 0),
            'customers_served': fleet_kpis.get('unique_customers', 0),
            'energy_kwh': fleet_kpis.get('total_energy_kwh', 0),
            'emissions_kg_co2': fleet_kpis.get('total_emissions_kg', 0),
            'avg_efficiency_kwh_km': fleet_kpis.get('fleet_avg_efficiency_kwh_km', 0),
            'emissions_per_tkm': fleet_kpis.get('emissions_per_tkm', 0)
        }
        
        monthly_metrics.append(monthly_summary)
    
    return pd.DataFrame(monthly_metrics)

def calculate_route_efficiency(trips_data: pd.DataFrame, routes_data: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate efficiency metrics by route
    
    Args:
        trips_data: Trip data
        routes_data: Routes data with distances
    
    Returns:
        DataFrame with route efficiency metrics
    """
    if trips_data.empty or routes_data.empty:
        return pd.DataFrame()
    
    # Create route column in trips data
    trips_data = trips_data.copy()
    trips_data['route'] = trips_data['from_location'].astype(str) + ' → ' + trips_data['to_location'].astype(str)
    
    # Group by route
    route_stats = trips_data.groupby(['from_location', 'to_location']).agg({
        'date': 'count',  # Trip frequency
        'tons_loaded': ['sum', 'mean'],  # Total and average cargo
        'distance_km': 'first',  # Distance (should be same for all trips on route)
        'plate_number': 'nunique'  # Number of different trucks used
    }).round(2)
    
    # Flatten column names
    route_stats.columns = ['trip_count', 'total_cargo_tons', 'avg_cargo_tons', 'distance_km', 'trucks_used']
    
    # Calculate route metrics
    route_stats['total_tkm'] = route_stats['total_cargo_tons'] * route_stats['distance_km']
    route_stats['avg_utilization'] = route_stats['avg_cargo_tons']  # Could be enhanced with truck capacity data
    route_stats['frequency_per_month'] = route_stats['trip_count'] / 1  # Assuming 1 month period, adjust as needed
    
    return route_stats.reset_index()

def validate_calculation_inputs(trips_data: pd.DataFrame, energy_data: pd.DataFrame) -> List[str]:
    """
    Validate input data for calculations
    
    Args:
        trips_data: Trip data to validate
        energy_data: Energy data to validate
    
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Validate trips data
    if trips_data.empty:
        errors.append("Trip data is empty")
    else:
        required_trip_columns = ['plate_number', 'distance_km', 'tons_loaded']
        for col in required_trip_columns:
            if col not in trips_data.columns:
                errors.append(f"Missing required column in trip data: {col}")
            elif trips_data[col].isnull().any():
                errors.append(f"Null values found in trip data column: {col}")
        
        # Check for negative values
        if 'distance_km' in trips_data.columns and (trips_data['distance_km'] < 0).any():
            errors.append("Negative distances found in trip data")
        
        if 'tons_loaded' in trips_data.columns and (trips_data['tons_loaded'] < 0).any():
            errors.append("Negative cargo weights found in trip data")
    
    # Validate energy data
    if not energy_data.empty:
        required_energy_columns = ['plate_number', 'kwh_per_km']
        for col in required_energy_columns:
            if col not in energy_data.columns:
                errors.append(f"Missing required column in energy data: {col}")
        
        # Check for unrealistic efficiency values
        if 'kwh_per_km' in energy_data.columns:
            unrealistic_high = (energy_data['kwh_per_km'] > 10).any()
            unrealistic_low = (energy_data['kwh_per_km'] <= 0).any()
            
            if unrealistic_high:
                errors.append("Unrealistically high energy consumption values found (>10 kWh/km)")
            
            if unrealistic_low:
                errors.append("Zero or negative energy consumption values found")
    
    # Check data consistency
    if not trips_data.empty and not energy_data.empty:
        trip_trucks = set(trips_data['plate_number'].unique())
        energy_trucks = set(energy_data['plate_number'].unique())
        
        missing_energy = trip_trucks - energy_trucks
        if missing_energy:
            errors.append(f"Missing energy data for trucks: {', '.join(missing_energy)}")
    
    return errors

def calculate_carbon_intensity(trips_data: pd.DataFrame, energy_data: pd.DataFrame,
                             emission_factor: float = 0.5) -> float:
    """
    Calculate fleet carbon intensity (kg CO2 per ton-kilometer)
    
    Args:
        trips_data: Trip data
        energy_data: Energy consumption data
        emission_factor: CO2 emission factor in kg CO2/kWh
    
    Returns:
        Carbon intensity value
    """
    fleet_kpis = calculate_fleet_kpis(trips_data, energy_data, emission_factor)
    return fleet_kpis.get('emissions_per_tkm', 0)

def benchmark_truck_performance(truck_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Benchmark individual truck performance against fleet averages
    
    Args:
        truck_metrics: DataFrame with truck performance metrics
    
    Returns:
        DataFrame with benchmark comparisons
    """
    if truck_metrics.empty:
        return pd.DataFrame()
    
    benchmarked = truck_metrics.copy()
    
    # Calculate fleet averages for benchmarking
    fleet_avg_efficiency = truck_metrics['kwh_per_km'].mean()
    fleet_avg_emissions_per_km = truck_metrics['kg_co2_per_km'].mean()
    fleet_avg_emissions_per_tkm = truck_metrics['kg_co2_per_tkm'].mean()
    
    # Calculate performance vs fleet average (percentage difference)
    benchmarked['efficiency_vs_fleet'] = (
        (truck_metrics['kwh_per_km'] - fleet_avg_efficiency) / fleet_avg_efficiency * 100
    ).round(1)
    
    benchmarked['emissions_per_km_vs_fleet'] = (
        (truck_metrics['kg_co2_per_km'] - fleet_avg_emissions_per_km) / fleet_avg_emissions_per_km * 100
    ).round(1)
    
    benchmarked['emissions_per_tkm_vs_fleet'] = (
        (truck_metrics['kg_co2_per_tkm'] - fleet_avg_emissions_per_tkm) / fleet_avg_emissions_per_tkm * 100
    ).round(1)
    
    # Add performance categories
    benchmarked['efficiency_category'] = benchmarked['efficiency_vs_fleet'].apply(
        lambda x: 'Excellent' if x < -10 else 'Good' if x < 0 else 'Average' if x < 10 else 'Needs Improvement'
    )
    
    return benchmarked
