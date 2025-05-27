import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# Set wide layout, inject CSS/HTML for a beautiful header (only ONCE)
st.set_page_config(layout="wide")

st.markdown("""
<style>
.header-title {
  font-size: 2.2em;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 0.6em;
  margin-bottom: 0.2em;
}
.header-sep {
  width: 100%;
  height: 4px;
  border: none;
  border-radius: 2px;
  background: linear-gradient(90deg, #ff512f, #f09819, #ffe259, #f09819, #ff512f);
  margin-bottom: 32px;
}
</style>
<div class="header-title">📍 Valiasr Street Memories</div>
<hr class="header-sep">
""", unsafe_allow_html=True)

# ========== Google Sheets setup ==========
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GSPREAD_SA_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open(st.secrets["SHEET_NAME"]).worksheet("valiasr_memories")

# ========== Load data ==========
data = sheet.get_all_records()
df = pd.DataFrame(data)
df.columns = [col.strip() for col in df.columns]
df["row_id"] = df.index + 2  # row_id for delete button
memory_json = json.dumps(df.to_dict(orient="records"))

# ========== Receive data from JS via query params ==========
query = st.query_params

if "lat" in query:
    try:
        lat = float(query["lat"])
        lon = float(query["lon"])
        user_type = query["user_type"]
        message = query["message"]
        sheet.append_row([lat, lon, user_type, message])
        st.success("✅ Memory saved!")
        st.markdown(
            "<script>window.location.href = window.location.pathname;</script>",
            unsafe_allow_html=True
        )
        st.stop()
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.markdown(
            "<script>window.location.href = window.location.pathname;</script>",
            unsafe_allow_html=True
        )
        st.stop()

if "delete_row" in query:
    try:
        sheet.delete_rows(int(query["delete_row"]))
        st.success("🗑 Row deleted.")
        st.markdown(
            "<script>window.location.href = window.location.pathname;</script>",
            unsafe_allow_html=True
        )
        st.stop()
    except Exception as e:
        st.error(f"❌ Error deleting: {e}")
        st.markdown(
            "<script>window.location.href = window.location.pathname;</script>",
            unsafe_allow_html=True
        )
        st.stop()


# ========== Inject Google Maps & Memory Form ==========
components.html(f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Map</title>
    <style>
      #map {{ height: 600px; width: 100%; }}
      .form-popup {{
        background: white;
        border-radius: 10px;
        padding: 10px;
        width: 250px;
        font-family: Arial;
      }}
      .form-popup input, .form-popup select, .form-popup textarea {{
        width: 100%; margin-top: 5px;
      }}
      .form-popup button {{ margin-top: 10px; width: 48%; }}
    </style>
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDi9TbBUZ33JQS3wU4DDCi4t2RvqbXAs_4"></script>
    <script>
      let map;
      let infowindow = null;
      function initMap() {{
        map = new google.maps.Map(document.getElementById("map"), {{
          center: {{ lat: 35.7448, lng: 51.3880 }},
          zoom: 13
        }});

        infowindow = new google.maps.InfoWindow();

        const memories = {memory_json};
        memories.forEach(mem => {{
          const marker = new google.maps.Marker({{
            position: {{ lat: parseFloat(mem.lat), lng: parseFloat(mem.lon) }},
            map: map,
            icon: mem.user_type === "pedestrian" ? 'http://maps.google.com/mapfiles/ms/icons/green-dot.png' :
                  mem.user_type === "vehicle_passenger" ? 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png' :
                  'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
          }});

          const popup = new google.maps.InfoWindow({{
            content: `<b>User:</b> ${{mem.user_type}}<br><b>Memory:</b> ${{mem.message}}<br>
                      <button onclick='window.location.href=\"?delete_row=${{mem.row_id}}\"'>🗑 Delete</button>`
          }});

          marker.addListener('click', () => popup.open(map, marker));
        }});

        map.addListener("click", function(e) {{
          const lat = e.latLng.lat().toFixed(6);
          const lon = e.latLng.lng().toFixed(6);
          const formHTML = `
            <div class='form-popup'>
              <label>User type:</label>
              <select id='userType'>
                <option value='pedestrian'>Pedestrian</option>
                <option value='vehicle_passenger'>Vehicle Passenger</option>
                <option value='traveler'>Traveler</option>
              </select>
              <label>Memory:</label>
              <textarea id='memoryText' rows='3'></textarea>
              <div style='display: flex; justify-content: space-between;'>
                <button onclick='submitMemory(${{lat}}, ${{lon}})'>Save</button>
                <button onclick='infowindow.close()'>Cancel</button>
              </div>
            </div>`;
          infowindow.setContent(formHTML);
          infowindow.setPosition(e.latLng);
          infowindow.open(map);
        }});
      }}

      function submitMemory(lat, lon) {{
        const userType = document.getElementById('userType').value;
        const message = document.getElementById('memoryText').value;
        const params = new URLSearchParams({{
          lat: lat,
          lon: lon,
          user_type: userType,
          message: message
        }});
        window.location.href = `?${{params.toString()}}`;
      }}

      window.onload = initMap;
    </script>
  </head>
  <body>
    <div id="map"></div>
  </body>
</html>
""", height=620)
