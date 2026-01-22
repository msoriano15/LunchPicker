import streamlit as st
import requests
import random
import folium
import time
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium

# --- CONFIGURATION ---
OFFICE_ADDRESS = "Åsögatan 115, 117 68 Stockholm" # <--- Change to your office!

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
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
@st.cache_data(show_spinner=False)
def get_coords(address):
    try:
        geolocator = Nominatim(user_agent="office_lunch_app_v3")
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

lat, lon = get_coords(OFFICE_ADDRESS)

if lat:
    if not st.session_state.places:
        raw_data = fetch_osm_data(lat, lon, distance)
        st.session_state.places = [p for p in raw_data if 'tags' in p and 'name' in p['tags']]

    if st.button("🎲 SPIN THE WHEEL"):
        if st.session_state.places:
            # Loading Sequence
            msgs = ["Scanning area...", "Filtering by vibe...", "Finalizing choice..."]
            status = st.empty()
            for m in msgs:
                status.text(m)
                time.sleep(0.5)
            status.empty()
            
            winner = random.choice(st.session_state.places)
            st.session_state.winner_info = {
                'name': winner['tags'].get('name'),
                'cuisine': winner['tags'].get('cuisine', 'Food').capitalize(),
                'lat': winner.get('lat', winner.get('center', {}).get('lat')),
                'lon': winner.get('lon', winner.get('center', {}).get('lon'))
            }
        else:
            st.warning("No spots found nearby.")

    st.divider()

    # DISPLAY THE RESULT
    if st.session_state.winner_info:
        res = st.session_state.winner_info
        
        # Black Card
        st.markdown(f"""
            <div class="result-card">
                <h2 style="color: white; margin: 0;">{res['name']}</h2>
                <p style="margin: 5px 0 0 0; opacity: 0.8;">🍴 {res['cuisine']}</p>
            </div>
            """, unsafe_allow_html=True)

        col_map, col_share = st.columns([3, 1])
        
        with col_share:
            st.write("📢 **Share**")
            st.markdown(f"""
                <a href="https://slack.com/app_redirect?channel=general" target="_blank" style="text-decoration:none;">
                    <button style="width:100%; background-color:#4A154B; color:white; border:none; padding:8px; border-radius:5px; margin-bottom:5px; cursor:pointer;">Slack</button>
                </a>
                <a href="https://teams.microsoft.com/l/chat/0/0?users=" target="_blank" style="text-decoration:none;">
                    <button style="width:100%; background-color:#464EB8; color:white; border:none; padding:8px; border-radius:5px; cursor:pointer;">Teams</button>
                </a>
            """, unsafe_allow_html=True)
            
            if st.button("📋 Copy"):
                st.code(f"Lunch: {res['name']} ({res['cuisine']})")

        with col_map:
            m = folium.Map(location=[res['lat'], res['lon']], zoom_start=17)
            folium.Marker([res['lat'], res['lon']], popup=res['name'], icon=folium.Icon(color='black')).add_to(m)
            folium.Marker([lat, lon], popup="Office", icon=folium.Icon(color='gray')).add_to(m)
            st_folium(m, width=500, height=300, key="lunch_map_final")
        
        st.markdown(f"### [↗️ Open Directions](https://www.google.com/maps/dir/?api=1&origin={lat},{lon}&destination={res['lat']},{res['lon']}&travelmode=walking)")
    else:
        st.info("Click the button to decide lunch!")
else:
    st.error("Address not found. Check the code!")
