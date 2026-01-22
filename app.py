import streamlit as st
import requests
import random
import folium
import time
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

# --- CONFIGURATION ---
OFFICE_ADDRESS = "Times Square, New York" # <--- Change to your office!

st.set_page_config(page_title="Team Lunch Roulette", page_icon="🍕", layout="centered")

# --- STYLING ---
st.markdown("""
    <style>
    /* The Big Black Spin Button */
    .stButton>button { 
        width: 100%; border-radius: 10px; height: 3.5em; 
        background-color: #000000; color: #ffffff; 
        font-weight: bold; font-size: 1.2rem; border: 2px solid #000000;
    }
    .stButton>button:hover { background-color: #333333; border: 2px solid #333333; color: white; }
    
    /* Custom Result Card */
    .result-card {
        background-color: #000000; color: #ffffff; 
        padding: 20px; border-radius: 10px; margin-bottom: 20px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
@st.cache_data(show_spinner=False)
def get_coords(address):
    try:
        geolocator = Nominatim(user_agent="office_lunch_app_final")
        location = geolocator.geocode(address, timeout=10)
        return (location.latitude, location.longitude) if location else (None, None)
    except:
        return None, None

@st.cache_data(show_spinner="Searching neighborhood...")
def fetch_osm_data(lat, lon, radius):
    url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (node["amenity"~"restaurant|cafe|fast_food|pub"](around:{radius},{lat},{lon});
     way["amenity"~"restaurant|cafe|fast_food|pub"](around:{radius},{lat},{lon}););
    out center;
    """
    try:
        response = requests.get(url, params={'data': query}, timeout=10)
        return response.json().get('elements', [])
    except:
        return []

# --- STATE MANAGEMENT ---
if 'winner_info' not in st.session_state:
    st.session_state.winner_info = None
if 'places' not in st.session_state:
    st.session_state.places = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    distance = st.slider("Walking distance (m)", 200, 2000, 600)
    if st.button("🔄 Reset App"):
        st.session_state.clear()
        st.rerun()

# --- MAIN APP UI ---
st.title("🍕 Team Lunch Roulette")
st.write(f"Near: **{OFFICE_ADDRESS}**")

lat, lon = get_coords(
