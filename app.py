import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 時區與初始化 (確保 4/5 就是 4/5) ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

# 記憶目前選中的成員，預設為 IRENE
if "current_user" not in st.session_state:
    st.session_state.current_user = "IRENE"

# --- 1. 頁面設定 ---
st.set_page_config(page_title="CAL Crew Hub", page_icon="✈️", layout="wide")

# 🌸 核心名冊顏色設定 (Master Data)
CREW_CONFIG = {
    "IRENE": {"color": "#F07699", "icon": "🌸"},
    "ISABELLE": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}

# 確保選中的人在名冊內，防止 KeyError
if st.session_state.current_user not in CREW_CONFIG:
    st.session_state.current_user = "IRENE"

user_color = CREW_CONFIG[st.session_state.current_user]["color"]
BG_BLACK = "#0E0E0E"

# --- 2. 終極 CSS 鎖定 (防藍色、大字體、動態邊框) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 側邊欄邊框隨人變色 */
    [data-testid="stSidebar"] {{
        background-color: #151515;
        border-right: 2px solid {user_color};
    }}
    
    /* 月曆格子底色與大白字鎖死 */
    .fc-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        background: {user_color} !important;
    }}
    .fc-event-title {{
        font-size: 2.0em !important; 
        font-weight: 900 !important;
        color: white !important;
        text-align: center !important;
    }}

    /* 詳情卡片與標籤 */
    .report-card {{
        background: #1F1F1F; border-radius: 15px; padding: 22px;
        border: 2px solid {user_color}; margin-bottom: 15px;
        box-shadow: 0 0 15px {user_color}33;
    }}
    .tag {{
        background: {user_color}; color: white; padding: 4px 10px;
        border-radius: 6px; font-size: 0.8rem; font-weight: 800;
    }}

    /* 側邊欄按鈕樣式 */
    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 800; width: 100%; height: 3.5em; border-radius: 10px;
        transition: 0.3s;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. 數據讀取與處理 (ETL 流程) ---
try:
    # A. 讀取所有人班表 (crew_roster.csv)
    all_rosters = pd.read_csv('crew_roster.csv', encoding='utf-8-sig')
    all_rosters.columns = all_rosters.columns.str.strip()
    
    # B. 讀取航班詳情 (my_flights.csv)
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # C. 過濾目前選中者的月曆事件
    user_df = all_rosters[all_rosters['姓名'] == st.session_state.current_user]
    calendar_events = []
    for _, row in user_df.iterrows():
        calendar_events.append({
            "title": str(row['班號']),
            "start": str(row['日期']),
            "end": str(row['日期']),
            "allDay": True
        })
except Exception as e:
    st.error(f"❌ 數據讀取錯誤，請檢查 CSV 檔案: {e}")
    st.stop()

# --- 4. 側邊欄導航 (Left Frame) ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{user_color}; text-align:center;'>✈️ CREW MENU</h2>", unsafe_allow_html=True)
    
    # 建立四位戰友的切換按鈕
    for name, config in CREW_CONFIG.items():
        label = f"{config['icon']} {name}"
        if st.button(label, key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
            
    st.divider()
    
    # TODAY 快捷鍵
    if st.button(f"📍 TODAY'S FLIGHT"):
        today_match = user_df[user_df['日期'] == today_str]
        st.session_state.sel_f = today_match['班號'].iloc[0] if not today_match.empty else "None"
    
    st.divider()
    st.subheader("📋 Flight Details")
    details_placeholder = st.empty()

# --- 5. 主頁面月曆 ---
st.title(f"💖 {st.session_state.current_user}'S CALENDAR")

calendar_options = {
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
    "initialView": "dayGridMonth",
    "initialDate": today_str,
    "contentHeight": "auto",
}
state = calendar(events=calendar_events, options=calendar_options, key=f"cal_{st.session_state.current_user}")

# --- 6. 詳情連動顯示 ---
target = None
if state.get("eventClick"):
    target = state["eventClick"]["event"]["title"].strip()
elif "sel_f" in st.session_state:
    target = str(st.session_state.sel_f)

with details_placeholder.container():
    if target and target != "None":
        stay_list = ["150", "151", "130", "131", "731", "732"]
        s_list = [target]
        if target not in stay_list:
            try: s_list.append(str(int(target) + 1))
            except: pass
            
        for t in s_list:
            match = flight_db[flight_db['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                tag = "GO" if (len(s_list)>1 and t==target) else ("RTN" if len(s_list)>1 else "STAY")
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{user_color}; margin:0;'>CI {t}</h2>
                            <span class="tag">{tag}</span>
                        </div>
                        <p style='margin:15px 0 5px 0; font-size:1.4rem; font-weight:700;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.1rem;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:15px 0;'>
                        <p style='margin:0; font-size:1rem; color:#AAA;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
    elif target == "None":
        st.info("今天放假！好好休息 ☕")
    else:
        st.write("✨ 點擊月曆查看班表詳情")
