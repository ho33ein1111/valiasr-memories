import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(layout="wide")
st.title("📍 Khaterehaye Khiaban Valiasr - Tehran")

csv_file = "pins.csv"

# Load or init data
try:
    df = pd.read_csv(csv_file)
except:
    df = pd.DataFrame(columns=["lat", "lon", "user_type", "message"])

# Google Maps HTML (interactive map with JS postMessage)
st.markdown("### 🗺️ Rooye naghshe click kon:")

components.html(f"""
<!DOCTYPE html>
<html>
  <head>
    <title>Google Maps Clickable</title>
    <meta name="viewport" content="initial-scale=1.0">
    <meta charset="utf-8">
    <style>
      #map {{
        height: 500px;
        width: 100%;
      }}
    </style>
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyD1SKh6VhTZDTBEx4V2FD6zTSqRb3nSwAw"></script>
    <script>
      function initMap() {{
        const center = {{ lat: 35.7448, lng: 51.3880 }};
        const map = new google.maps.Map(document.getElementById("map"), {{
          zoom: 13,
          center: center,
        }});

        map.addListener("click", (e) => {{
          const lat = e.latLng.lat().toFixed(6);
          const lon = e.latLng.lng().toFixed(6);
          new google.maps.Marker({{
            position: e.latLng,
            map: map,
          }});
          window.parent.postMessage({{ type: "map-click", lat: lat, lon: lon }}, "*");
        }});
      }}
    </script>
  </head>
  <body onload="initMap()">
    <div id="map"></div>
  </body>
</html>
""", height=500)

# JS listener to update query params
components.html("""
<script>
window.addEventListener("message", (event) => {
  if (event.data.type === "map-click") {
    const query = new URLSearchParams(window.location.search);
    query.set("clicked_lat", event.data.lat);
    query.set("clicked_lon", event.data.lon);
    window.location.search = query.toString();
  }
});
</script>
""", height=0)

# Get query params
params = st.query_params
lat = params.get("clicked_lat", [None])[0]
lon = params.get("clicked_lon", [None])[0]

# Show form if click exists
if lat and lon:
    lat, lon = float(lat), float(lon)
    st.success(f"📌 Location entekhab shod: {lat:.4f}, {lon:.4f}")

    with st.form("memory_form"):
        user_type = st.selectbox("Noe karbar", ["rahro-piade", "rahro-savar", "mosafer"])
        message = st.text_area("Matn khatere", max_chars=200)
        submitted = st.form_submit_button("📌 Sabt Khatere")

        if submitted and message.strip():
            new_row = pd.DataFrame([[lat, lon, user_type, message]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(csv_file, index=False)
            st.success("✅ Khatere sabt shod! Safhe ro reload kon ta pin-ha ro bebin.")
else:
    st.info("⬅️ Click kon rooye naghshe baraye entekhab location.")
