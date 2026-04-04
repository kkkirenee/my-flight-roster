import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL Calendar", page_icon="📅", layout="wide")

HOT_PINK = "#FF2E63"
BG_BLACK = "#0E0E0E"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .report-card {{
        background: #1A1A1A; border-radius: 15px; padding: 25px;
        border: 1px solid {HOT_PINK}; box-shadow: 0 0 15px rgba(255,46,99,0.2);
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 班表資料 ---
ROSTER = {
    "2026-04-03": "116", "2026-04-05": "517", "2026-04-08": "108",
    "2026-04-10": "915", "2026-04-12": "150", "2026-04-13": "151",
    "2026-04-14": "130", "2026-04-15": "131", "2026-04-16": "527", 
    "2026-04-18": "731", "2026-04-19": "732", "2026-04-21": "186", 
    "2026-04-23": "783", "2026-04-25": "190", "2026-04-30": "156"
}

calendar_events = []
for date, flight in ROSTER.items():
    calendar_events.append({
        "title": f"{flight}", # ✨ 關鍵修改：拿掉 CI，只留數字
        "start": date,
        "end": date,
        "backgroundColor": HOT_PINK,
        "borderColor": HOT_PINK
    })

# --- 3. 讀取 CSV ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
except:
    st.error("找不到 my_flights.csv")
    st.stop()

# --- 4. 顯示介面 ---
st.title("💖 FLIGHT CALENDAR")

col1, col2 = st.columns([2.5, 1])

with col1:
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth",
        },
        "initialView": "dayGridMonth",
        "selectable": True,
        "contentHeight": "auto",
        "eventDisplay": "block",
    }
    
    custom_css = """
        .fc-event-title {
            font-size: 1.4em !important; /* 數字可以再稍微大一點 */
            font-weight: 800 !important;
            padding: 5px !important;
            text-align: center !important;
        }
        .fc-daygrid-event {
            margin-top: 2px !important;
        }
    """
    
    state = calendar(
        events=calendar_events, 
        options=calendar_options, 
        custom_css=custom_css,
        key="roster_cal"
    )

with col2:
    st.subheader("📋 Flight Details")
    
    if state.get("eventClick"):
        # 取得點擊的純數字標題
        search_no = state["eventClick"]["event"]["title"].strip()
        
        # 在 CSV 的「班號」欄位搜尋包含這個數字的列
        match = df[df['班號'].astype(str).str.contains(search_no)]
        
        if not match.empty:
            r = match.iloc[0]
            st.markdown(f"""
                <div class="report-card">
                    <h2 style='color:{HOT_PINK}; margin:0;'>{r['班號']}</h2>
                    <p>📍 <b>目的地:</b> {r['目的地']}</p>
                    <p>⏰ <b>報到:</b> <span style='color:{HOT_PINK}'>{r.get('報到時間', '--:--')}</span></p>
                    <hr style='border-color:#333'>
                    <p>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.write("點擊月曆上的航班查看詳情")
