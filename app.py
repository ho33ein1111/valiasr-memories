import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("📍 Memories from Valiasr Street - Tehran")

csv_file = "pins.csv"

# Load existing data or initialize new
try:
    df = pd.read_csv(csv_file)
except:
    df = pd.DataFrame(columns=["lat", "lon", "user_type", "message"])

# Create the base map
m = folium.Map(location=[35.7448, 51.3880], zoom_start=13)

# Add existing pins to the map
color_map = {
    "pedestrian": "green",
    "vehicle_passenger": "blue",
    "traveler": "red"
}

for _, row in df.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f'{row["user_type"]}: {row["message"]}',
        icon=folium.Icon(color=color_map.get(row["user_type"], "gray"))
    ).add_to(m)

# Display the map and detect clicks
st.markdown("### 🗺️ Click on the map to select a location:")
map_data = st_folium(m, width=700, height=500, returned_objects=["last_clicked"])

# If user clicked on the map
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📌 Location selected: {lat:.4f}, {lon:.4f}")

    with st.form("memory_form"):
        user_type = st.selectbox("Who are you?", ["pedestrian", "vehicle_passenger", "traveler"])
