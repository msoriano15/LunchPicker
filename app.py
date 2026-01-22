import streamlit as st
import requests
import random
import folium
from geopy.geocoders import Nominatim
from streamlit_folium import st_folium
from streamlit_extras.let_it_rain import rain

# --- CONFIGURATION ---
OFFICE_ADDRESS = "ÅSÖGATAN 115, 116 24 STOCKHOLM, SWEDEN " # <--- Change this to your office!

st.set_page_config(page_title="Team Lunch Roulette", page_icon="🍕")

# Custom CSS for a cleaner look
st.markdown("""
    <style>
    .main { text-align: center; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCTIONS ---
@st.cache_data
def get_coords(address):
    geolocator = Nominatim(user_agent="office_lunch_app")
    location = geolocator.geocode(address)
    return (location.latitude, location.longitude) if location else (None, None)

def fetch_osm_data(lat, lon, radius):
    url = "http://overpass-api.de/api/interpreter"
    query = f"""
    [out:json];
    (node["amenity"~"restaurant|cafe|fast_food|pub"](around:{radius},{lat},{lon});
     way["amenity"~"restaurant|cafe|fast_food|pub"](around:{radius},{lat},{lon}););
    out center;
    """
    response = requests.get(url, params={'data': query})
    return response.json().get('elements', [])

# --- APP UI ---
st.title("🍕 Team Lunch Roulette")
st.write(f"Based near: **{OFFICE_ADDRESS}**")

# Sidebar Filters
with st.sidebar:
    st.header("Settings")
    distance = st.slider("Walking distance (m)", 200, 2000, 600)
    show_map = st.checkbox("Show map", value=True)
    if st.button("Reset Session"):
        st.session_state.clear()

# Logic to get location
lat, lon = get_coords(OFFICE_ADDRESS)

if lat:
    if 'places' not in st.session_state:
        raw_data = fetch_osm_data(lat, lon, distance)
        # Filter for places that have a name
        st.session_state.places = [p for p in raw_data if 'tags' in p and 'name' in p['tags']]

    if st.button("🎲 SPIN THE WHEEL"):
        if st.session_state.places:
            winner = random.choice(st.session_state.places)
            st.session_state.last_winner = winner
            
            # Interactive "Rain" effect
            rain(emoji="🥗", font_size=54, falling_speed=5, animation_length="short")
            
            # Display Result
            name = winner['tags'].get('name')
            cuisine = winner['tags'].get('cuisine', 'Food').capitalize()
            
            st.success(f"### We're going to: {name}")
            st.info(f"🍴 Style: {cuisine}")
            
            # Coordinates for Map
            w_lat = winner.get('lat', winner.get('center', {}).get('lat'))
            w_lon = winner.get('lon', winner.get('center', {}).get('lon'))
            
            if show_map:
                m = folium.Map(location=[w_lat, w_lon], zoom_start=17)
                folium.Marker([w_lat, w_lon], popup=name, tooltip=name, icon=folium.Icon(color='red')).add_to(m)
                folium.Marker([lat, lon], popup="Office", icon=folium.Icon(color='blue', icon='briefcase')).add_to(m)
                st_folium(m, width=700, height=300)
                
            st.markdown(f"[↗️ Open in Google Maps](https://www.google.com/maps/search/?api=1&query={w_lat},{w_lon})")
        else:
            st.error("No places found. Try a larger distance in the sidebar!")
else:
    st.error("Could not find office coordinates. Check your address!")

st.divider()
st.caption("Data provided for free by OpenStreetMap")