import streamlit as st
from utils.left_pane import setup_left_pane
from utils.header import inject_top_header

st.set_page_config(page_title="Dashboard Overview", page_icon="🚛", layout="wide")

setup_left_pane()                      # draws the blue strip; ideally sets --dsv-left-pane-width
inject_top_header("Dashboard Overview")  # puts the title into the real top header


# ---- Page content ----
st.markdown("""
### Welcome to the EV Truck Performance Tracking System

This application helps you track and analyze the performance of your electric vehicle fleet. Use the navigation menu to access different sections:

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
""")
