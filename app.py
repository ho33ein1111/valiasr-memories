import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GSPREAD_SA_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open(st.secrets["SHEET_NAME"]).sheet1

# Load data
st.set_page_config(layout="wide")
st.title("📍 Valiasr Street Memories")

data = sheet.get_all_records()
df = pd.DataFrame(data)
df.columns = [col.strip() for col in df.columns]
df["row_id"] = df.index + 2
memory_json = json.dumps(df.to_dict(orient="records"))

# Handle update
query = st.query_params
if "update_row" in query:
    try:
        row_id = int(query["update_row"])
        new_user_type = query["edit_user_type"]
        new_message = query["edit_message"]
        cell_user_type = f"C{row_id}"
        cell_message = f"D{row_id}"
        sheet.update(cell_user_type, new_user_type)
        sheet.update(cell_message, new_message)
        st.success("✏️ Memory updated!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error updating: {e}")

# Handle save
if "lat" in query:
    try:
        lat = float(query["lat"])
        lon = float(query["lon"])
        user_type = query["user_type"]
        message = query["message"]
        sheet.append_row([lat, lon, user_type, message])
        st.success("✅ Memory saved!")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error: {e}")

# Handle delete
if "delete_row" in query:
    try:
        sheet.delete_rows(int(query["delete_row"]))
        st.success("🗑 Row deleted.")
        st.experimental_rerun()
    except Exception as e:
        st.error(f"❌ Error deleting: {e}")

# Inject map and JS
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
            content: `<b>User:</b> ${{{{mem.user_type}}}}<br>
                      <b>Memory:</b> ${{{{mem.message}}}}<br>
                      <button onclick='window.location.href=\"?delete_row=${{{{mem.row_id}}}}\"'>🗑 Delete</button>
                      <button onclick='showEditForm(${{{{mem.row_id}}}}, \"${{{{mem.user_type}}}}\", \"${{{{mem.message.replace(/\"/g, '&quot;')}}}}\")'>✏️ Edit</button>`
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
                <button onclick='submitMemory(${{\"{{\"}}lat{{\"}}\"}}, ${{\"{{\"}}lon{{\"}}\"}})'>Save</button>
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
        window.location.href = `?${{params.toString()}}`;
      }}

      function showEditForm(row_id, user_type, message) {{
        // Decode HTML entities
        message = message.replace(/&quot;/g, '\"');
        const formHTML = `
          <div class='form-popup'>
            <label>User type:</label>
            <select id='editUserType'>
              <option value='pedestrian' ${{{{user_type=='pedestrian'?'selected':''}}}}>Pedestrian</option>
              <option value='vehicle_passenger' ${{{{user_type=='vehicle_passenger'?'selected':''}}}}>Vehicle Passenger</option>
              <option value='traveler' ${{{{user_type=='traveler'?'selected':''}}}}>Traveler</option>
            </select>
            <label>Memory:</label>
            <textarea id='editMemoryText' rows='3'>${{{{message}}}}</textarea>
            <div style='display: flex; justify-content: space-between;'>
              <button onclick='submitEdit(${{{{row_id}}}})'>Update</button>
              <button onclick='infowindow.close()'>Cancel</button>
            </div>
          </div>`;
        infowindow.setContent(formHTML);
        infowindow.open(map);
      }}

      function submitEdit(row_id) {{
        const userType = document.getElementById('editUserType').value;
        const message = document.getElementById('editMemoryText').value;
        const params = new URLSearchParams({{
          update_row: row_id,
          edit_user_type: userType,
          edit_message: message
        }});
        window.location.href = `?${{params.toString()}}`;
      }}

      let infowindow = null;
      window.onload = function() {{
        infowindow = new google.maps.InfoWindow();
        initMap();
      }};
    </script>
  </head>
  <body>
    <div id="map"></div>
  </body>
</html>
""", height=620)
