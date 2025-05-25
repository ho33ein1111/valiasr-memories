import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")
st.title("📍 خاطرات خیابان ولیعصر - تهران")

csv_file = "pins.csv"

# بارگذاری داده‌های موجود یا ایجاد دیتافریم جدید
try:
    df = pd.read_csv(csv_file)
except FileNotFoundError:
    df = pd.DataFrame(columns=["lat", "lon", "user_type", "message"])

st.markdown("### 🗺️ روی نقشه کلیک کنید تا مکان انتخاب شود:")

# ایجاد نقشه با Folium
m = folium.Map(location=[35.7448, 51.3880], zoom_start=13)

# افزودن نشانگرها از داده‌های موجود
color_map = {
    "rahro-piade": "green",
    "rahro-savar": "blue",
    "mosafer": "red"
}

for _, row in df.iterrows():
    folium.Marker(
        location=[row["lat"], row["lon"]],
        popup=f'{row["user_type"]}: {row["message"]}',
        icon=folium.Icon(color=color_map.get(row["user_type"], "gray"))
    ).add_to(m)

# نمایش نقشه و دریافت کلیک کاربر
map_data = st_folium(m, width=700, height=500)

# بررسی کلیک کاربر
if map_data and map_data["last_clicked"]:
    lat = map_data["last_clicked"]["lat"]
    lon = map_data["last_clicked"]["lng"]
    st.success(f"📌 مکان انتخاب شده: {lat:.4f}, {lon:.4f}")

    with st.form("memory_form"):
        user_type = st.selectbox("نوع کاربر", ["rahro-piade", "rahro-savar", "mosafer"])
        message = st.text_area("متن خاطره", max_chars=200)
        submitted = st.form_submit_button("📌 ثبت خاطره")

        if submitted and message.strip():
            new_row = pd.DataFrame([[lat, lon, user_type, message]], columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(csv_file, index=False)
            st.success("✅ خاطره ثبت شد! برای مشاهده، صفحه را مجدداً بارگذاری کنید.")
else:
    st.info("⬅️ روی نقشه کلیک کنید تا مکان انتخاب شود.")
