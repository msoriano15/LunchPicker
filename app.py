import streamlit as st
import requests
import random
import folium
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
from streamlit_extras.let_it_rain import rain

# --- CONFIGURATION ---
# Change this to your actual office address!
OFFICE_ADDRESS = "ÅSÖGATAN 115, 116 24 STOCKHOLM, SWEDEN" 

st.set_page_config(page_title="Team Lunch Roulette", page_icon="🍕", layout="centered")

# --- STYLING ---
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 20px; height: 3.5em; 
        background-color: #ff4b4b; color: white; font-weight: bold; font-size: 1.2rem; }
    .stButton>button:hover { border: 2px solid #ff4b4b; color: #ff4b4b; background-color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
@st.cache_data(show_spinner=False)
def get_coords(address):
    try:
        geolocator = Nominatim(user_agent="office_lunch_app_v2")
        location = geolocator.geocode(address, timeout=10)
        return (location.latitude, location.longitude) if location else (None, None)
    except:
        return None, None

@st.cache_data(show_spinner="Fetching local spots...")
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
# This stops the "glitch" by saving the winner in memory
if 'winner_info' not in st.session_state:
    st.session_state.winner_info = None
if 'places' not in st.session_state:
    st.session_state.places = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Settings")
    distance = st.slider("Walking distance (meters)", 200, 2000, 600)
    st.divider()
    if st.button("🔄 Clear App Cache"):
        st.cache_data.clear()
        st.session_state.clear()
        st.rerun()

# --- MAIN APP UI ---
st.title("🍕 Team Lunch Roulette")
st.write(f"Finding food near: **{OFFICE_ADDRESS}**")

lat, lon = get_coords(OFFICE_ADDRESS)

if lat:
    # 1. Fetch data if we don't have it yet
    if not st.session_state.places:
        raw_data = fetch_osm_data(lat, lon, distance)
        st.session_state.places = [p for p in raw_data if 'tags' in p and 'name' in p['tags']]

    # 2. The Spin Button
    if st.button("🎲 SPIN THE WHEEL"):
        if st.session_state.places:
            winner = random.choice(st.session_state.places)
            
            # Save winner details to session state so they don't disappear on rerun
            st.session_state.winner_info = {
                'name': winner['tags'].get('name'),
                'cuisine': winner['tags'].get('cuisine', 'Food').capitalize(),
                'lat': winner.get('lat', winner.get('center', {}).get('lat')),
                'lon': winner.get('lon', winner.get('center', {}).get('lon'))
            }
            # Visual flair
            rain(emoji="🥗", font_size=54, falling_speed=4, animation_length="short")
        else: