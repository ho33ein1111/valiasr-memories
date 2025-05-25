import streamlit as st
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("🧪 Test: Click Detection on Map")

m = folium.Map(location=[35.7448, 51.3880], zoom_start=13)

map_data = st_folium(m, height=500, width=700, returned_objects=["last_clicked"])

st.markdown("---")
st.subheader("📍 Click Result")
st.write(map_data)

if map_data and map_data.get("last_clicked"):
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"You clicked: {lat:.4f}, {lon:.4f}")
