import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 時區與初始化 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

# 如果沒有選擇任何人，預設選妳自己
if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

# --- 1. 頁面設定 ---
st.set_page_config(page_title="Team Calendar", page_icon="📅", layout="wide")

HOT_PINK = "#F07699"
SOFT_BLUE = "#7699F0" # 幫第二個人換個顏色做區隔
BG_BLACK = "#0E0E0E"

# --- 2. 班表資料庫 (多人模式) ---
# 這裡可以無限擴充，以後有新同事就加進去
USERS_DATA = {
    "Irene": {
        "color": HOT_PINK,
        "roster": {
            "2026-04-03": "116", "2026-04-05": "517", "2026-04-08": "108",
            "2026-04-10": "915", "2026-04-12": "150", "2026-04-13": "151"
        }
    },
    "學姐": {
        "color": SOFT_BLUE,
        "roster": {
            "2026-04-03": "108", "2026-04-04": "511", "2026-04-06": "156",
            "2026-04-10": "731", "2026-04-12": "116", "2026-04-15": "915"
        }
    }
}

# --- 3. CSS 樣式鎖定 ---
user_color = USERS_DATA[st.session_state.current_user]["color"]

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    /* 強制月曆格子顏色隨人改變 */
    .fc-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
    }}
    
    .report-card {{
        background: #222222; border-radius: 15px; padding: 20px;
        border: 1px solid {user_color}; margin-bottom: 12px;
    }}
    .tag {{ background: {user_color}; color: white; padding: 3px 10px; border-radius: 5px; }}
    
    /* 側邊欄按鈕樣式 */
    div.stButton > button {{
        background-color: #333; color: white; border: 1px solid #444;
        font-weight: 800; width: 100%; margin-bottom: 10px;
    }}
    /* 被選中的按鈕變亮色 */
    div.stButton > button:focus {{
        background-color: {user_color}; color: white; border: none;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 側邊欄 (左側按鈕選單) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{user_color};'>👥 Team Roster</h2>", unsafe_allow_html=True)
    st.write("選擇要查看的成員：")
    
    # 為每個人建立一個切換按鈕
    for name in USERS_DATA.keys():
        if st.button(f"👤 {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun() # 點擊後重新整理頁面以切換資料
            
    st.divider()
    st.subheader("📋 Flight Details")
    details_placeholder = st.empty()

# --- 5. 處理目前選中者的資料 ---
current_user = st.session_state.current_user
user_info = USERS_DATA[current_user]
current_roster = user_info["roster"]

calendar_events = []
for d, f in current_roster.items():
    calendar_events.append({"title": f, "start": d, "end": d, "allDay": True})

# --- 6. 主頁面 (右側月曆) ---
st.title(f"💖 {current_user}'s Calendar")

calendar_options = {
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
    "initialView": "dayGridMonth",
    "initialDate": today_str,
    "contentHeight": 700,
}
custom_css = ".fc-event-title { font-size: 1.6em !important; font-weight: 900 !important; text-align: center !important; }"
state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key=f"cal_{current_user}")

# --- 7. 顯示詳情 (CSV 讀取與匹配) ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['班號'] = df['班號'].astype(str).str.replace('CI', '').str.strip()
    
    target = None
    if state.get("eventClick"):
        target = state["eventClick"]["event"]["title"].strip()
        
    with details_placeholder.container():
        if target:
            match = df[df['班號'] == target]
            if not match.empty:
                r = match.iloc[0]
                st.markdown(f"""
                    <div class="report-card">
                        <h2 style='color:{user_color}; margin:0;'>CI {target}</h2>
                        <p style='margin:10px 0;'>📍 <b>{r['目的地']}</b></p>
                        <p style='font-size:0.9rem;'>⏰ 報到: {r.get('報到時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.write("點擊月曆查看航班詳情")
except:
    st.sidebar.error("CSV 讀取失敗")
