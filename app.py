import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

st.set_page_config(layout="wide")
st.title("📍 خاطرات خیابان ولیعصر")

csv_file = "pins.csv"

try:
    df = pd.read_csv(csv_file)
except:
    df = pd.DataFrame(columns=["lat", "lon", "user_type", "message"])

color_map = {
    "rahro-piade": "green",
    "rahro-savar": "blue",
    "mosafer": "red"
}

m = folium.Map(location=[35.7448, 51.3880], zoom_start=13)

for i, row in df.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f'{row["user_type"]}: {row["message"]}',
        icon=folium.Icon(color=color_map.get(row["user_type"], "gray"))
    ).add_to(m)

st.markdown("### 🗺️ click on map to create a memory:")
map_data = st_folium(m, height=500, width=700, returned_objects=["last_clicked"])

if map_data is not None and map_data.get("last_clicked") is not None:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]

    st.success(f"📌 Location entekhab shod: {lat:.4f}, {lon:.4f}")

    with st.form("memory_form"):
        user_type = st.selectbox("Noe karbar", ["rahro-piade", "rahro-savar", "mosafer"])
        message = st.text_area("Matn khatere", max_chars=200)
        submitted = st.form_submit_button("📌 Sabt Khatere")

        if submitted and message.strip():
            new_row = pd.DataFrame([[lat, lon, user_type, message]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(csv_file, index=False)
            st.success("✅ Khatere sabt shod! Baraye didan bayad safhe reload beshe.")
else:
    st.info("⬅️ Click kon rooye naghshe baraye entekhab location.")
