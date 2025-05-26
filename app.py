import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import streamlit.components.v1 as components

# --- Google Sheets setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GSPREAD_SA_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open(st.secrets["SHEET_NAME"]).sheet1

# --- UI config ---
st.set_page_config(layout="wide")
st.title("📍 Valiasr Street Memories")

# --- Load existing data ---
rows = sheet.get_all_records()
memory_data = []
for i, row in enumerate(rows, start=2):
    row["row_id"] = i
    memory_data.append(row)

memory_json = json.dumps(memory_data)

# --- Display map with JS ---
components.html(f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
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
  <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyAs4WWVHuqIR6e1AGAoOG6KdGn3hM4zook"></script>
  <script>
    let map;
    function initMap() {{
      map = new google.maps.Map(document.getElementById("map"), {{
        center: {{ lat: 35.7448, lng: 51.3880 }},
        zoom: 13
      }});

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
          content: `<b>User:</b> ${{mem.user_type}}<br>
                    <b>Memory:</b> ${{mem.message}}<br>
                    <button onclick='window.location.search="?delete_row=${{mem.row_id}}"'>🗑 Delete</button>`
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
              <button onclick='submitMemory(${{"{{"}}lat{{"}}"}}, ${{"{{"}}lon{{"}}"}})'>Save</button>
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
      const params = new URLSearchParams({{
        lat: lat,
        lon: lon,
        user_type: userType,
        message: message
      }});
      window.location.search = '?' + params.toString();
    }}

    window.onload = initMap;
  </script>
</head>
<body>
  <div id="map"></div>
</body>
</html>
""", height=620)

# --- Handle query parameters ---
query = st.query_params

if "lat" in query:
    try:
        sheet.append_row([
            float(query["lat"]),
            float(query["lon"]),
            query["user_type"],
            query["message"]
        ])
        st.success("✅ Memory saved!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error saving: {e}")

if "delete_row" in query:
    try:
        sheet.delete_row(int(query["delete_row"]))
        st.success("🗑 Row deleted.")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error deleting: {e}")
