import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_folium import st_folium
import folium
import json
import os

st.set_page_config(layout="wide")
st.title("📍 Memories from Valiasr Street - Tehran")

# Load Google Sheets credentials from secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GSPREAD_SA_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Access the sheet
sheet_name = st.secrets["SHEET_NAME"]
sheet = client.open(sheet_name).sheet1

# Load data from sheet
data = sheet.get_all_records()
df = pd.DataFrame(data)

# Set up map
m = folium.Map(location=[35.7448, 51.3880], zoom_start=13)

color_map = {
    "pedestrian": "green",
    "vehicle_passenger": "blue",
    "traveler": "red"
}

for _, row in df.iterrows():
    popup_html = f"""
    <b>User type:</b> {row["user_type"]}<br>
    <b>Memory:</b> {row["message"]}
    """
    popup = folium.Popup(popup_html, max_width=300)
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=popup,
        icon=folium.Icon(color=color_map.get(row["user_type"], "gray"))
    ).add_to(m)

# Show map and get click
st.markdown("### 🗺️ Click on the map to select a location:")
map_data = st_folium(m, width=700, height=500, returned_objects=["last_clicked"])

if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📌 Location selected: {lat:.4f}, {lon:.4f}")

    with st.form("memory_form"):
        user_type = st.selectbox("Who are you?", ["pedestrian", "vehicle_passenger", "traveler"])
        message = st.text_area("Write your memory here:", max_chars=200)
        submitted = st.form_submit_button("📌 Submit Memory")

        if submitted and message.strip():
            sheet.append_row([lat, lon, user_type, message])
            st.success("✅ Memory saved! Refresh to see it on the map.")
else:
    st.info("⬅️ Click on the map to choose a location.")
