import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

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
df["row_id"] = df.index + 2  # row_id for delete/update
memory_json = json.dumps(df.to_dict(orient="records"))

# ========== Handle query params for Save, Delete, Edit ==========
query = st.query_params

if "lat" in query and "edit_row" not in query:
    # New memory
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

if "edit_row" in query and "lat" in query:
    # Update memory
    try:
        row_id = int(query["edit_row"])
        lat = float(query["lat"])
        lon = float(query["lon"])
        user_type = query["user_type"]
        message = query["message"]
        # Google Sheets update_cells uses A1 notation, but we know row_id (2-based)
        sheet.update(f"A{row_id}:D{row_id}", [[lat, lon, user_type, message]])
        st.success("✅ Memory updated!")
        st.markdown(
            "<script>window.location.href = window.location.pathname;</script>",
            unsafe_allow_html=True
        )
        st.stop()
    except Exception as e:
        st.error(f"❌ Error updating: {e}")
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

      function getMemories() {{
        return {memory_json};
      }}

      function initMap() {{
        map = new google.maps.Map(document.getElementById("map"), {{
          center: {{ lat: 35.7448, lng: 51.3880 }},
          zoom: 13
        }});
        infowindow = new google.maps.InfoWindow();

        // Draw all pins
        const memories = getMemories();
        memories.forEach(mem => {{
          const marker = new google.maps.Marker({{
            position: {{ lat: parseFloat(mem.lat), lng: parseFloat(mem.lon) }},
            map: map,
            icon: mem.user_type === "pedestrian" ? 'http://maps.google.com/mapfiles/ms/icons/green-dot.png' :
                  mem.user_type === "vehicle_passenger" ? 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png' :
                  'http://maps.google.com/mapfiles/ms/icons/red-dot.png'
          }});

          const popupContent = `
            <b>User:</b> ${{mem.user_type}}<br>
            <b>Memory:</b> ${{mem.message}}<br>
            <button onclick='window.location.href="?delete_row=${{mem.row_id}}"'>🗑 Delete</button>
            <button onclick="openEditForm(${{mem.row_id}}, ${{mem.lat}}, ${{mem.lon}}, '${{mem.user_type}}', '${{mem.message.replace(/'/g, "\\'")}}')">✏️ Edit</button>
          `;
          const popup = new google.maps.InfoWindow({{
            content: popupContent
          }});

          marker.addListener('click', () => popup.open(map, marker));
        }});

        // New memory form
        map.addListener("click", function(e) {{
          openMemoryForm(e.latLng.lat().toFixed(6), e.latLng.lng().toFixed(6));
        }});
      }}

      function openMemoryForm(lat, lon) {{
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
        infowindow.setPosition({{lat: parseFloat(lat), lng: parseFloat(lon)}});
        infowindow.open(map);
      }}

      function openEditForm(row_id, lat, lon, user_type, message) {{
        // Escape html for textarea value!
        message = message.replace(/"/g, '&quot;');
        const formHTML = `
          <div class='form-popup'>
            <label>User type:</label>
            <select id='userType'>
              <option value='pedestrian' ${'{'}user_type=='pedestrian'?'selected':''{'}'}>Pedestrian</option>
              <option value='vehicle_passenger' ${'{'}user_type=='vehicle_passenger'?'selected':''{'}'}>Vehicle Passenger</option>
              <option value='traveler' ${'{'}user_type=='traveler'?'selected':''{'}'}>Traveler</option>
            </select>
            <label>Memory:</label>
            <textarea id='memoryText' rows='3'>${'{'}message{'}'}</textarea>
            <div style='display: flex; justify-content: space-between;'>
              <button onclick='submitEdit(${{row_id}}, ${{lat}}, ${{lon}})'>Update</button>
              <button onclick='infowindow.close()'>Cancel</button>
            </div>
          </div>`;
        infowindow.setContent(formHTML);
        infowindow.setPosition({{lat: parseFloat(lat), lng: parseFloat(lon)}});
        infowindow.open(map);
        setTimeout(() => {{
          document.getElementById('userType').value = user_type;
        }}, 50);
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

      function submitEdit(row_id, lat, lon) {{
        const userType = document.getElementById('userType').value;
        const message = document.getElementById('memoryText').value;
        const params = new URLSearchParams({{
          edit_row: row_id,
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
