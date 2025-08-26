import streamlit as st
from utils.left_pane import setup_left_pane
from utils.header import inject_top_header

st.set_page_config(page_title="Dashboard Overview", page_icon="🚛", layout="wide")

setup_left_pane()
inject_top_header("Dashboard Overview")

# --- Hard kill ALL top spacers (Streamlit + Replit wrapper) ---
st.markdown("""
<style>
/* 1) Replit/host wrappers that sometimes add top space */
body, .stApp, .main, #root { margin-top: 0 !important; padding-top: 0 !important; }
div[style*="position: sticky"][style*="top: 0"] { margin-top: 0 !important; }

/* 2) Streamlit’s own header/toolbars/decoration that push content down */
header[data-testid="stHeader"] { margin-bottom: 0 !important; padding-bottom: 0 !important; }
div[data-testid="stDecoration"] { display: none !important; }     /* thin color bar */
div[data-testid="stToolbar"] { display: none !important; }        /* File | Rerun toolbar */
div[data-testid="stStatusWidget"] { display: none !important; }   /* status pill */

/* 3) Remove ALL top padding under header and kill the “phantom” first block gap */
section.main > div.block-container { padding-top: 0 !important; margin-top: 0 !important; }
section.main > div.block-container > div[data-testid="stVerticalBlock"]:first-child {
  margin-top: 0 !important;
  padding-top: 0 !important;
  min-height: 0 !important;
}

/* 4) If the host still injects a spacer, force a negative pull-up (tweak if needed) */
section.main > div.block-container { transform: translateY(-16px); }
@media (max-width: 640px) { section.main > div.block-container { transform: translateY(-10px); } }
</style>
""", unsafe_allow_html=True)

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
