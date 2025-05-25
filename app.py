import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("📍 Memories from Valiasr Street - Tehran")

csv_file = "pins.csv"

# Load or initialize data
try:
    df = pd.read_csv(csv_file)
except:
    df = pd.DataFrame(columns=["lat", "lon", "user_type", "message"])

# Create the map
m = folium.Map(location=[35.7448, 51.3880], zoom_start=13)

# Add previous pins
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

# Show the map and handle clicks
st.markdown("### 🗺️ Click on the map to select a location:")
map_data = st_folium(m, width=700, height=500, returned_objects=["last_clicked"])

# If user clicked on map
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📌 Location selected: {lat:.4f}, {lon:.4f}")

    with st.form("memory_form"):
        user_type = st.selectbox("Who are you?", ["pedestrian", "vehicle_passenger", "traveler"])
        message = st.text_area("Write your memory here:", max_chars=200)
        submitted = st.form_submit_button("📌 Submit Memory")  # ✅ FIXED — this line was missing before

        if submitted and message.strip():
            new_row = pd.DataFrame([[lat, lon, user_type, message]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(csv_file, index=False)
            st.success("✅ Memory saved! Refresh the page to see it on the map.")
else:
    st.info("⬅️ Click on the map to choose a location.")
