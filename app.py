import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheets setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GSPREAD_SA_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open(st.secrets["SHEET_NAME"]).sheet1

# --- Streamlit config ---
st.set_page_config(layout="wide")
st.title("📍 Valiasr Street Memories - Interactive Map")

# --- Load existing data from Google Sheet ---
data = sheet.get_all_records()
df = pd.DataFrame(data)
df.columns = [col.strip() for col in df.columns]  # strip spaces if any

# --- Send data to JS map ---
memory_data = df.to_dict(orient="records")

components.html(f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Google Map Memory Map</title>
    <style>
      #map {{ height: 600px; width: 100%; }}
      .form-popup {{
        background: white;
        border-radius: 10px;
        padding: 10px;
        width: 250px;
        font-family: Arial;
      }}
      .form-popup input, .form-popup select, .form-popup textarea {{ width: 100%; margin-top: 5px; }}
      .form-popup button {{ margin-top: 10px; width: 48%; }}
    </style>
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAs4WWVHuqIR6e1AGAoOG6KdGn3hM4zook"></script>
    <script>
      let map;
      function initMap() {{
        map = new google.maps.Map(document.getElementById("map"), {{
          center: {{ lat: 35.7448, lng: 51.3880 }},
          zoom: 13,
        }});

        const memories = {json.dumps(memory_data)};
        memories.forEach(mem => {{
          const marker = new google.maps.Marker({{
            position: {{ lat: parseFloat(mem.lat), lng: parseFloat(mem.lon) }},
            map: map,
            icon: mem.user_type === "pedestrian" ? 'http://maps.google.com/mapfiles/ms/icons/green-dot.png' :
                  mem.user_type === "vehicle_passenger" ? 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png' :
                  'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
          }});

          const popup = new google.maps.InfoWindow({{
            content: `<b>User:</b> ${mem.user_type}<br><b>Memory:</b> ${mem.message}`
          }});

          marker.addListener('click', () => popup.open(map, marker));
        }});

        map.addListener("click", (e) => {{
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
                <button onclick='submitMemory({lat}, {lon})'>Save</button>
                <button onclick='infowindow.close()'>Cancel</button>
              </div>
            </div>`;

          infowindow = new google.maps.InfoWindow({{
            content: formHTML,
            position: e.latLng
          }});
          infowindow.open(map);
        }});
      }}

      function submitMemory(lat, lon) {{
        const userType = document.getElementById('userType').value;
        const message = document.getElementById('memoryText').value;
        const payload = {{ lat: lat, lon: lon, user_type: userType, message: message }};
        parent.postMessage(payload, '*');
        infowindow.close();
      }}

      window.onload = initMap;
    </script>
  </head>
  <body>
    <div id="map"></div>
  </body>
</html>
""", height=620)

# --- Receive data from JS ---
received = st.experimental_get_query_params()

if received.get("lat"):
    try:
        lat = float(received["lat"][0])
        lon = float(received["lon"][0])
        user_type = received["user_type"][0]
        message = received["message"][0]

        sheet.append_row([lat, lon, user_type, message])
        st.success("✅ Memory saved!")
    except Exception as e:
        st.error(f"Error saving memory: {e}")
