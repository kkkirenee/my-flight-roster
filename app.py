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
        margin-bottom: 15px; /* 卡片之間的間距 */
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 班表資料 (4月) ---
# 注意：當天來回班，我們在 ROSTER 裡用半形逗號 "," 隔開兩個班號
ROSTER = {
    "2026-04-03": "116", "2026-04-05": "517", "2026-04-08": "108",
    "2026-04-10": "915", "2026-04-12": "150", 
    "2026-04-13": "150,151", # ✨ 當天來回範例：去程 150，回程 151
    "2026-04-14": "130", 
    "2026-04-15": "130,131", # ✨ 當天來回範例
    "2026-04-16": "527", 
    "2026-04-18": "731", 
    "2026-04-19": "731,732", # ✨ 當天來回範例
    "2026-04-21": "186", "2026-04-23": "783", "2026-04-25": "190", "2026-04-30": "156"
}

calendar_events = []
for date, flight_str in ROSTER.items():
    # 月曆標題：如果是來回班，顯示如 "150/151"
    display_title = flight_str.replace(",", "/")
    calendar_events.append({
        "title": display_title,
        "start": date,
        "end": date,
        "backgroundColor": HOT_PINK,
        "borderColor": HOT_PINK
    })

# --- 3. 讀取 CSV ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['班號'] = df['班號'].astype(str)
except:
    st.error("找不到 my_flights.csv")
    st.stop()

# --- 4. 顯示介面 ---
st.title("💖 FLIGHT CALENDAR")

col1, col2 = st.columns([2.5, 1])

with col1:
    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "selectable": True,
        "contentHeight": "auto",
        "eventDisplay": "block",
    }
    
    custom_css = ".fc-event-title { font-size: 1.3em !important; font-weight: 800 !important; padding: 5px !important; text-align: center !important; }"
    
    state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key="roster_cal")

with col2:
    st.subheader("📋 Flight Details")
    
    if state.get("eventClick"):
        # 取得點擊標題並拆分（處理來回班）
        clicked_title = state["eventClick"]["event"]["title"]
        flight_nos = clicked_title.split("/") # 把 150/151 拆成 ['150', '151']
        
        found_any = False
        for f_no in flight_nos:
            search_no = f_no.strip()
            # 精準匹配 CSV 裡的班號
            match = df[df['班號'].str.contains(search_no)]
            
            if not match.empty:
                r = match.iloc[0]
                found_any = True
                st.markdown(f"""
                    <div class="report-card">
                        <h2 style='color:{HOT_PINK}; margin:0;'>CI {search_no}</h2>
                        <p>📍 <b>目的地:</b> {r['目的地']}</p>
                        <p>⏰ <b>報到:</b> <span style='color:{HOT_PINK}'>{r.get('報到時間', '--:--')}</span></p>
                        <hr style='border-color:#333'>
                        <p>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        if not found_any:
            st.warning("找不到對應的航班資料。")
    else:
        st.write("點擊月曆上的航班查看詳情")
