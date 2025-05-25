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

# Load mapbox click JS
st.markdown("### 🗺️ Rooye naghshe click kon:")
components.html(f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>Mapbox Clickable Map</title>
<meta name="viewport" content="initial-scale=1,maximum-scale=1,user-scalable=no" />
<style>
  body {{ margin: 0; padding: 0; }}
  #map {{ position: absolute; top: 0; bottom: 0; width: 100%; height: 500px; }}
</style>
<script src="https://api.mapbox.com/mapbox-gl-js/v2.13.0/mapbox-gl.js"></script>
<link href="https://api.mapbox.com/mapbox-gl-js/v2.13.0/mapbox-gl.css" rel="stylesheet" />
</head>
<body>
<div id="map"></div>
<script>
mapboxgl.accessToken = 'pk.eyJ1IjoiZGVtb3VzZXIiLCJhIjoiY2tzbDYxNjFsMDVrdjJubGlydzMxaDh1diJ9.3XYjWT1qZP4rp-WWRA6kCg';
const map = new mapboxgl.Map({{
  container: 'map',
  style: 'mapbox://styles/mapbox/streets-v11',
  center: [51.3880, 35.7448],
  zoom: 13
}});
map.on('click', function (e) {{
    const coords = e.lngLat;
    const lat = coords.lat.toFixed(6);
    const lon = coords.lng.toFixed(6);
    window.parent.postMessage({{
        type: 'map-click',
        lat: lat,
        lon: lon
    }}, '*');
}});
</script>
</body>
</html>
""", height=500)

# JS bridge handler
clicked = st.experimental_get_query_params()
lat = st.session_state.get("clicked_lat", None)
lon = st.session_state.get("clicked_lon", None)

# Inject JS listener
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

# Read click from URL query
params = st.experimental_get_query_params()
if "clicked_lat" in params and "clicked_lon" in params:
    lat = float(params["clicked_lat"][0])
    lon = float(params["clicked_lon"][0])
    st.session_state.clicked_lat = lat
    st.session_state.clicked_lon = lon
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
