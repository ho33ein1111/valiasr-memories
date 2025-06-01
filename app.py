import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# ========== Google Sheets setup ==========
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GSPREAD_SA_JSON"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open(st.secrets["SHEET_NAME"]).worksheet("valiasr_memories")

# ========== Load data ==========
st.set_page_config(layout="wide")
st.title("📍 Valiasr Street Memories")

def escape_js_string(s):
    if not isinstance(s, str):
        return ""
    return (
        s.replace("\\", "\\\\")
         .replace("'", "\\'")
         .replace('"', '&quot;')
         .replace("\n", " ")
         .replace("\r", " ")
    )

data = sheet.get_all_records()
df = pd.DataFrame(data)
df.columns = [col.strip() for col in df.columns]
df["row_id"] = df.index + 2  # 2-based for gspread
df["js_user_type"] = df["user_type"].apply(escape_js_string)
df["js_message"] = df["message"].apply(escape_js_string)
memory_json = json.dumps(df.to_dict(orient="records"))

# ========== Receive data from JS via query params ==========
query = st.query_params

if "update_row" in query:
    try:
        row_id = int(query["update_row"])
        new_user_type = query["edit_user_type"]
        new_message = query["edit_message"]
        sheet.update(f"C{row_id}:C{row_id}", [[new_user_type]])
        sheet.update(f"D{row_id}:D{row_id}", [[new_message]])
        st.success("✏️ Memory updated!")
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error updating: {e}")
        st.query_params.clear()
        st.rerun()

if "lat" in query:
    try:
        lat = float(query["lat"])
        lon = float(query["lon"])
        user_type = query["user_type"]
        message = query["message"]
        sheet.append_row([lat, lon, user_type, message])
        st.success("✅ Memory saved!")
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error: {e}")
        st.query_params.clear()
        st.rerun()

if "delete_row" in query:
    try:
        sheet.delete_rows(int(query["delete_row"]))
        st.success("🗑 Row deleted.")
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"❌ Error deleting: {e}")
        st.query_params.clear()
        st.rerun()

# ========== Inject Google Maps & Memory Form ==========
components.html(f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <title>Map</title>
    <style>
      body {{ background: #f4f4f4; }}
      #map {{
        height: 620px; width: 100%; margin: 0; border-radius: 16px; box-shadow: 0 8px 32px rgba(80,80,120,.10);
      }}
      .form-popup {{
        background: #fff;
        border-radius: 18px;
        box-shadow: 0 6px 18px rgba(60,60,80,.09);
        padding: 22px 16px 10px 16px;
        width: 270px;
        font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
        font-size: 1.04em;
        letter-spacing: 0.01em;
      }}
      .form-popup label {{
        font-weight: 500; color: #666; margin-top: 8px;
      }}
      .form-popup select, .form-popup textarea {{
        width: 100%;
        margin-top: 5px;
        border-radius: 8px;
        border: 1px solid #d8d8d8;
        padding: 7px 10px;
        font-size: 1em;
        margin-bottom: 7px;
        background: #fcfcfc;
        transition: border 0.15s;
      }}
      .form-popup textarea:focus, .form-popup select:focus {{
        outline: none; border: 1.3px solid #8ab4f8;
      }}
      .form-popup button {{
        margin-top: 12px;
        width: 47%;
        padding: 7px 0;
        font-size: 1em;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        background: #f09819;
        color: white;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(250,175,70,0.11);
        transition: background .2s;
      }}
      .form-popup button:hover {{
        background: #ff512f;
      }}
      .popup-actions {{
        display: flex; justify-content: space-between; gap: 8px;
      }}
      .icon-btn {{
        background: #efefef !important;
        color: #b13f3f !important;
        font-size: 1.14em !important;
        border: 1.5px solid #ffebee !important;
        width: 42%;
        box-shadow: none !important;
      }}
      .icon-btn:hover {{
        background: #ffe5e5 !important;
        color: #ff512f !important;
      }}
      .edit-btn {{
        background: #51bb7b !important;
        color: #fff !important;
        border: none !important;
        width: 51%;
      }}
      .edit-btn:hover {{
        background: #38b183 !important;
      }}
    </style>
    <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyDi9TbBUZ33JQS3wU4DDCi4t2RvqbXAs_4"></script>
    <script>
      let map;
      let infowindow = null;
      function closeAllInfoWindows() {{
        if (infowindow) infowindow.close();
      }}
      function initMap() {{
        map = new google.maps.Map(document.getElementById("map"), {{
          center: {{ lat: 35.7448, lng: 51.3880 }},
          zoom: 13,
          styles: [
            {{
              featureType: "poi.business", elementType: "labels.icon", stylers: [{{ visibility: "off" }}]
            }},
            {{ featureType: "transit", elementType: "labels.icon", stylers: [{{ visibility: "off" }}] }}
          ]
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
          marker.addListener('click', () => {{
            closeAllInfoWindows();
            const safeUserType = String(mem.js_user_type);
            const safeMessage = String(mem.js_message);
            infowindow.setContent(
              `<div class='form-popup'>
                <b style='font-size:1.08em;color:#2d3446'>User:</b> <span style='color:#8ab4f8'>${{mem.user_type}}</span><br>
                <b style='font-size:1.08em;color:#2d3446'>Memory:</b> <span style='color:#444'>${{mem.message}}</span>
                <div class='popup-actions' style='margin-top:9px;'>
                  <button class="icon-btn" onclick='window.location.href="?delete_row=${{mem.row_id}}"'>🗑 Delete</button>
                  <button class="edit-btn" onclick="window.showEditForm(${{mem.row_id}}, '${{safeUserType}}', '${{safeMessage}}')">✏️ Edit</button>
                </div>
              </div>`
            );
            infowindow.open(map, marker);
          }});
        }});
        // New memory form
        map.addListener("click", function(e) {{
          closeAllInfoWindows();
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
              <div class='popup-actions'>
                <button onclick='submitMemory(${{lat}}, ${{lon}})'>Save</button>
                <button style="background:#ececec;color:#777" onclick='infowindow.close()'>Cancel</button>
              </div>
            </div>`;
          infowindow.setContent(formHTML);
          infowindow.setPosition(e.latLng);
          infowindow.open(map);
        }});
        // Edit popup (overrides preview popup)
        window.showEditForm = function(row_id, user_type, message) {{
          closeAllInfoWindows();
          message = message.replace(/&quot;/g, '"');
          const formHTML = `
            <div class='form-popup'>
              <label>User type:</label>
              <select id='editUserType'>
                <option value='pedestrian' ${{user_type=='pedestrian'?'selected':''}}>Pedestrian</option>
                <option value='vehicle_passenger' ${{user_type=='vehicle_passenger'?'selected':''}}>Vehicle Passenger</option>
                <option value='traveler' ${{user_type=='traveler'?'selected':''}}>Traveler</option>
              </select>
              <label>Memory:</label>
              <textarea id='editMemoryText' rows='3'>${{message}}</textarea>
              <div class='popup-actions'>
                <button class="edit-btn" onclick='window.submitEdit(${{row_id}})'>Update</button>
                <button class="icon-btn" onclick='infowindow.close()'>Cancel</button>
              </div>
            </div>`;
          infowindow.setContent(formHTML);
          infowindow.open(map);
        }};
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
      window.submitEdit = function(row_id) {{
        const userType = document.getElementById('editUserType').value;
        const message = document.getElementById('editMemoryText').value;
        const params = new URLSearchParams({{
          update_row: row_id,
          edit_user_type: userType,
          edit_message: message
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
""", height=640)
