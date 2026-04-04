import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import pytz

# --- 0. 時區校準 (台灣時區) ---
# 強制抓取台北時間，避免伺服器時差導致 5 號變成 4 號
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL Calendar", page_icon="📅", layout="wide")

HOT_PINK = "#FF2E63"
BG_BLACK = "#0E0E0E"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {HOT_PINK}; box-shadow: 0 0 20px rgba(255,46,99,0.3);
        margin-bottom: 15px;
    }}
    .tag {{
        background: {HOT_PINK}; color: white; padding: 4px 12px;
        border-radius: 6px; font-size: 0.9rem; font-weight: 900;
    }}
    /* 自定義 Today 大按鈕樣式 */
    div.stButton > button {{
        background-color: {HOT_PINK}; color: white; border: none;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
        font-size: 1.1rem; transition: 0.3s;
    }}
    div.stButton > button:hover {{
        background-color: #ff4d7d; transform: scale(1.02);
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
for date_key, flight in ROSTER.items():
    calendar_events.append({
        "title": flight, "start": date_key, "end": date_key,
        "backgroundColor": HOT_PINK, "borderColor": HOT_PINK
    })

# --- 3. 讀取 CSV ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['班號'] = df['班號'].astype(str).str.replace('CI', '').str.strip()
except:
    st.error("找不到 CSV 資料")
    st.stop()

# --- 4. 顯示介面 ---
st.title("💖 FLIGHT CALENDAR")

# 這裡點下去，我們直接強行把 target 設定為「今天的班號」
if st.button(f"📍 SHOW TODAY'S FLIGHT ({today_str})"):
    if today_str in ROSTER:
        st.session_state.selected_f = ROSTER[today_str]
    else:
        st.session_state.selected_f = "None"

col1, col2 = st.columns([2.5, 1])

with col1:
    calendar_options = {
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "initialDate": today_str,
        "contentHeight": "auto",
    }
    # 字體維持最大最粗
    custom_css = ".fc-event-title { font-size: 1.6em !important; font-weight: 900 !important; }"
    state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key="roster_cal")

with col2:
    st.subheader("📋 Flight Details")
    
    # 決定要抓哪一班的詳細資料
    final_target = None
    if state.get("eventClick"):
        final_target = state["eventClick"]["event"]["title"].strip()
    elif "selected_f" in st.session_state:
        final_target = st.session_state.selected_f

    if final_target and final_target != "None":
        stay_list = ["150", "151", "130", "131", "731", "732"]
        search_list = [final_target]
        # 如果不是過夜班，自動加一號
        if final_target not in stay_list:
            try: search_list.append(str(int(final_target) + 1))
            except: pass
            
        found = False
        for t in search_list:
            match = df[df['班號'].str.contains(t)]
            if not match.empty:
                r = match.iloc[0]
                found = True
                tag = "GO" if (len(search_list)>1 and t==final_target) else ("RTN" if len(search_list)>1 else "STAY")
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{HOT_PINK}; margin:0;'>CI {t}</h2>
                            <span class="tag">{tag}</span>
                        </div>
                        <p style='margin:15px 0 5px 0; font-size:1.3rem;'>📍 <b>{r['目的地']}</b></p>
                        <p style='font-size:1.1rem;'>⏰ 報到: <span style='color:{HOT_PINK}'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444;'>
                        <p style='margin:0; font-size:1.1rem;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
        if not found: st.warning(f"CSV 裡找不到 {final_target}")
    elif final_target == "None":
        st.info("今天沒有排班喔，好好休息！☕")
    else:
        st.write("點擊月曆班號，或按大按鈕看今天班表")
