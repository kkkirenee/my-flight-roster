import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime

# --- 0. 自動獲取今天日期 ---
# 2026-04-05
today_str = datetime.now().strftime("%Y-%m-%d")

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL Calendar", page_icon="📅", layout="wide")

HOT_PINK = "#FF2E63"
BG_BLACK = "#0E0E0E"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .report-card {{
        background: #1A1A1A; border-radius: 15px; padding: 20px;
        border: 1px solid {HOT_PINK}; box-shadow: 0 0 15px rgba(255,46,99,0.2);
        margin-bottom: 12px;
    }}
    .tag {{
        background: {HOT_PINK}; color: white; padding: 2px 8px;
        border-radius: 4px; font-size: 0.75rem; font-weight: 800;
    }}
    .fc .fc-day-today {{
        background: rgba(255, 46, 99, 0.2) !important;
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
        "title": flight, "start": date, "end": date,
        "backgroundColor": HOT_PINK, "borderColor": HOT_PINK
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
        "initialDate": today_str,
        "contentHeight": 650,
    }
    state = calendar(events=calendar_events, options=calendar_options, key="roster_cal")

with col2:
    st.subheader("📋 Flight Details")
    
    # --- 關鍵修正：優先判定「點擊」，若沒點擊則顯示「今天」 ---
    target_flight = None
    
    if state.get("eventClick"):
        target_flight = state["eventClick"]["event"]["title"].strip()
    elif today_str in ROSTER:
        target_flight = ROSTER[today_str]
        st.write(f"🌟 **今日班表預覽 ({today_str})**")

    if target_flight:
        stay_and_rtn_flights = ["150", "151", "130", "131", "731", "732"] 
        search_list = [target_flight]
        
        if target_flight not in stay_and_rtn_flights:
            try:
                val = int(target_flight)
                search_list.append(str(val + 1))
            except: pass
            
        for target in search_list:
            match = df[df['班號'].str.contains(target)]
            if not match.empty:
                r = match.iloc[0]
                tag_label = "GO" if (len(search_list) > 1 and target == target_flight) else ("RTN" if (len(search_list) > 1) else "STAY")
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between;'>
                            <h2 style='color:{HOT_PINK}; margin:0;'>CI {target}</h2>
                            <span class="tag">{tag_label}</span>
                        </div>
                        <p style='margin:10px 0 5px 0;'>📍 <b>目的地:</b> {r['目的地']}</p>
                        <p>⏰ <b>報到:</b> <span style='color:{HOT_PINK}'>{r.get('報到時間', '--:--')}</span></p>
                        <hr style='border-color:#333; margin:10px 0;'>
                        <p style='margin:0; font-size:0.9rem; opacity:0.8;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.write("✨ 點擊班號查看詳情")
