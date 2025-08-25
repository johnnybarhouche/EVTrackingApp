# EV Truck Performance Tracker

## Overview

EV Truck Performance Tracker is a Streamlit-based web application designed to monitor and analyze the performance of electric vehicle truck fleets. The application provides comprehensive tracking of truck trips, energy consumption, route optimization, and environmental impact analysis. It serves fleet managers who need to monitor operational efficiency, calculate carbon emissions, and optimize routes for electric commercial vehicles.

The system enables users to track individual trip data, monitor energy consumption patterns across different trucks, manage pickup/delivery locations, calculate route distances, and generate performance reports. The application emphasizes sustainability metrics by calculating CO2 emissions based on energy consumption and providing insights into fleet efficiency.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses Streamlit as the primary framework, implementing a multi-page architecture with session state management for data persistence. The main application entry point (app.py) initializes session state variables and page configuration, while individual features are organized into separate page modules under the `pages/` directory.

**Key architectural decisions:**
- **Multi-page structure**: Each major feature (Dashboard, Trips, Trucks, Locations, Routes, Data Import, Export, Debug) is implemented as a separate page module
- **Session state persistence**: All application data is stored in Streamlit's session state, providing persistence across page navigation without requiring a database
- **Modular design**: Business logic is separated into utility modules (`utils/`) for calculations, data processing, and external integrations

### Data Management
The application uses in-memory data storage through Pandas DataFrames stored in Streamlit session state. This approach eliminates the need for a persistent database while maintaining data consistency during user sessions.

**Core data structures:**
- **trips_data**: Contains trip records with customer, location, cargo, and truck information
- **trucks_data**: Stores calculated truck performance metrics and fleet statistics
- **locations_data**: Manages pickup/delivery locations with coordinates
- **routes_data**: Maintains route information with calculated distances
- **energy_consumption**: Tracks energy efficiency data per truck
- **emission_factor**: Configurable CO2 emission factor for environmental calculations

### Business Logic Layer
The `utils/` directory contains specialized modules for core business operations:

**calculations.py**: Implements truck performance metrics calculation, including total distance, energy consumption, ton-kilometers (freight work), and CO2 emissions. The module provides comprehensive fleet analytics by aggregating trip data and applying energy efficiency factors.

**data_processing.py**: Handles data validation and cleaning operations, ensuring data quality through type conversion, null value handling, and range validation for numeric fields.

**google_maps.py**: Provides integration with Google Maps Distance Matrix API for automatic route distance calculation, supporting both environment variable and Streamlit secrets configuration.

### User Interface Components
The application uses Plotly for interactive visualizations and data charts, providing users with graphical insights into fleet performance. Streamlit's native components handle forms, data tables, and file uploads.

**Visualization strategy**: Performance metrics are presented through interactive charts showing trends in energy consumption, distance traveled, and emissions over time, enabling data-driven decision making.

### Data Import/Export System
The application supports Excel file imports for bulk data loading and provides export functionality for generating reports. This design accommodates existing fleet management workflows where data may originate from other systems.

## External Dependencies

### Third-Party Libraries
- **Streamlit**: Web application framework providing the user interface and session management
- **Pandas**: Data manipulation and analysis library for handling trip data, calculations, and data processing
- **NumPy**: Numerical computing library supporting mathematical operations in performance calculations
- **Plotly**: Interactive visualization library for creating charts and graphs in the dashboard
- **Folium**: Map visualization library for displaying location data and route mapping
- **streamlit-folium**: Integration component for embedding Folium maps in Streamlit applications

### External APIs
- **Google Maps Distance Matrix API**: Used for calculating accurate driving distances between locations when automatic route calculation is enabled. The integration supports API key configuration through environment variables or Streamlit secrets.

### Environment Configuration
The application expects optional configuration through:
- **GOOGLE_MAPS_API_KEY**: Environment variable or Streamlit secret for Google Maps integration
- **Streamlit secrets**: Alternative configuration method for API keys in cloud deployments

### File System Dependencies
The application requires file system access for:
- **Excel file uploads**: Import functionality for trip data, locations, and energy consumption data
- **Data export**: Generation of Excel reports and CSV files for external analysis