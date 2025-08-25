import streamlit as st
import base64

def get_base64_of_image(path):
    """Convert image to base64 string for embedding in HTML"""
    try:
        with open(path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except:
        return None

def render_dsv_header():
    """Render the consistent DSV header across all pages"""
    # Get logo as base64
    logo_base64 = get_base64_of_image("assets/dsv_logo.png")
    
    if logo_base64:
        logo_html = f'<img src="data:image/png;base64,{logo_base64}" style="height: 40px; margin-right: 15px;">'
    else:
        logo_html = '<div style="background: white; color: #002664; padding: 0.5rem 1rem; border-radius: 4px; font-weight: bold; margin-right: 1rem; font-size: 1.2rem;">DSV</div>'
    
    header_html = f"""
    <div class="dsv-header">
        <div style="display: flex; align-items: center;">
            {logo_html}
            <h1 style="color: white; margin: 0; font-size: 1.8rem; font-weight: 600;">EV Truck Performance Tracker</h1>
        </div>
        <div style="color: white; font-size: 0.9rem; font-weight: 300;">
            Sustainability Dashboard
        </div>
    </div>
    """
    
    st.markdown(header_html, unsafe_allow_html=True)

def apply_dsv_styling():
    """Apply consistent DSV styling across all pages"""
    st.markdown("""
    <style>
        /* Import Roboto font */
        @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;600;700&display=swap');
        
        /* Main app styling */
        .stApp {
            background-color: #f8f9fa;
            font-family: 'Roboto', sans-serif;
        }
        
        /* DSV Header styling */
        .dsv-header {
            background-color: #002664;
            color: white;
            padding: 1rem 2rem;
            margin: -2rem -2rem 2rem -2rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            position: sticky;
            top: 0;
            z-index: 1000;
        }
        
        /* Sidebar styling */
        section[data-testid="stSidebar"] {
            background-color: #002664 !important;
        }
        
        section[data-testid="stSidebar"] > div {
            background-color: #002664 !important;
        }
        
        /* Sidebar navigation text - white by default */
        section[data-testid="stSidebar"] .css-10trblm,
        section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span {
            color: white !important;
        }
        
        /* Navigation links in sidebar */
        section[data-testid="stSidebar"] a {
            color: white !important;
            text-decoration: none !important;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            margin: 0.2rem 0;
            display: block;
            transition: all 0.3s ease;
        }
        
        /* Selected/active navigation item */
        section[data-testid="stSidebar"] a[aria-selected="true"],
        section[data-testid="stSidebar"] .css-1rs6os,
        section[data-testid="stSidebar"] .css-1vq4p4l .css-1rs6os {
            background-color: #002664 !important;
            color: white !important;
            font-weight: 600 !important;
            border-left: 4px solid white !important;
            padding-left: 1rem !important;
        }
        
        /* Hover effect for navigation items */
        section[data-testid="stSidebar"] a:hover {
            background-color: rgba(255,255,255,0.1) !important;
            color: white !important;
        }
        
        /* Main content area */
        .main .block-container {
            padding-top: 2rem;
            padding-left: 2rem;
            padding-right: 2rem;
            background-color: #f8f9fa;
        }
        
        /* Table headers - DSV blue background */
        .stDataFrame thead tr th,
        .stDataFrame thead th,
        thead tr th {
            background-color: #002664 !important;
            color: white !important;
            font-weight: 600 !important;
            border: none !important;
            padding: 12px !important;
        }
        
        /* Table styling */
        .stDataFrame table {
            border: 1px solid #ddd;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Table body styling */
        .stDataFrame tbody tr:nth-child(even) {
            background-color: #f8f9fa;
        }
        
        .stDataFrame tbody tr:hover {
            background-color: #e3f2fd;
        }
        
        /* Metrics styling - card design */
        [data-testid="metric-container"] {
            background: white;
            border: 1px solid #e0e0e0;
            padding: 1.5rem;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: box-shadow 0.3s ease;
        }
        
        [data-testid="metric-container"]:hover {
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        /* Button styling - DSV blue */
        .stButton > button {
            background-color: #002664;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
            font-size: 14px;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            background-color: #001a4d;
            color: white;
            box-shadow: 0 2px 8px rgba(0, 38, 100, 0.3);
        }
        
        /* Header styling */
        h1 {
            color: #002664 !important;
            font-weight: 600 !important;
            font-size: 2.5rem !important;
            margin-bottom: 1rem !important;
        }
        
        h2 {
            color: #002664 !important;
            font-weight: 500 !important;
            font-size: 1.8rem !important;
            margin-top: 2rem !important;
            margin-bottom: 1rem !important;
        }
        
        h3 {
            color: #002664 !important;
            font-weight: 500 !important;
            font-size: 1.4rem !important;
            margin-top: 1.5rem !important;
            margin-bottom: 0.75rem !important;
        }
        
        /* Expander styling */
        .streamlit-expanderHeader {
            background-color: #e8e8e8;
            border-radius: 6px;
            font-weight: 500;
        }
        
        /* Success/info/warning messages */
        .stAlert {
            border-radius: 6px;
            border-left: 4px solid #002664;
        }
        
        /* Form styling */
        .stForm {
            background: white;
            padding: 1.5rem;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input,
        .stSelectbox > div > div > div {
            border: 1px solid #d0d0d0;
            border-radius: 4px;
            padding: 0.5rem;
        }
        
        /* Charts container */
        .js-plotly-plot {
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        /* File uploader */
        .stFileUploader {
            background: white;
            border: 2px dashed #002664;
            border-radius: 8px;
            padding: 2rem;
            text-align: center;
        }
        
        /* Download button */
        .stDownloadButton > button {
            background-color: #002664;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.75rem 1.5rem;
            font-weight: 500;
        }
        
        .stDownloadButton > button:hover {
            background-color: #001a4d;
        }
    </style>
    """, unsafe_allow_html=True)