import streamlit as st
import requests
import random
from geopy.geocoders import Nominatim

st.set_page_config(page_title="Free Lunch Roulette", page_icon="🥪")

# 1. User Inputs
st.title("🥪 Free Lunch Decider")
st.markdown("Uses **OpenStreetMap** (No API keys required!)")

location_input = st.text_input("Where are you?", "Times Square, NY")
radius = st.slider("Walking Distance (meters)", 200, 2000, 500)

# 2. Function to get coordinates from address (Free via Nominatim)
@st.cache_data
def get_lat_lon(address):
    geolocator = Nominatim(user_agent="lunch_roulette_app_v1")
    location = geolocator.geocode(address)
    if location:
        return location.latitude, location.longitude
    return None, None

# 3. Function to fetch restaurants from OpenStreetMap
def get_restaurants_osm(lat, lon, radius):
    # Overpass Query Language
    # We ask for nodes, ways, and relations with amenity=restaurant around our lat/lon
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"~"restaurant|cafe|fast_food"](around:{radius},{lat},{lon});
      way["amenity"~"restaurant|cafe|fast_food"](around:{radius},{lat},{lon});
      relation["amenity"~"restaurant|cafe|fast_food"](around:{radius},{lat},{lon});
    );
    out center;
    """
    response = requests.get(overpass_url, params={'data': overpass_query})
    data = response.json()
    return data.get('elements', [])

# 4. The Logic
if st.button("Find Lunch! 🥗"):
    with st.spinner("Searching the map..."):
        lat, lon = get_lat_lon(location_input)
        
        if lat:
            results = get_restaurants_osm(lat, lon, radius)
            
            if results:
                # Filter out places without names
                valid_places = [r for r in results if 'tags' in r and 'name' in r['tags']]
                
                if valid_places:
                    choice = random.choice(valid_places)
                    name = choice['tags']['name']
                    cuisine = choice['tags'].get('cuisine', 'Unknown Cuisine').capitalize()
                    
                    # OSM returns 'center' for ways/relations, 'lat/lon' for nodes
                    c_lat = choice.get('lat', choice.get('center', {}).get('lat'))
                    c_lon = choice.get('lon', choice.get('center', {}).get('lon'))
                    
                    # Create a Google Maps link for directions
                    map_url = f"https://www.google.com/maps/search/?api=1&query={c_lat},{c_lon}"

                    st.success(f"🎉 Winner: **{name}**")
                    st.write(f"🍽️ Cuisine: {cuisine}")
                    st.markdown(f"[📍 Get Directions]({map_url})")
                    
                    # Optional: Show raw data if you want to see what OSM gives you
                    with st.expander("See raw data"):
                        st.json(choice)
                else:
                    st.warning("Found places, but none had names! (OSM data can be messy)")
            else:
                st.error("No restaurants found nearby. Try increasing the distance.")
        else:
            st.error("Could not find that location. Try a different address.")
