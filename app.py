import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 時區與初始化 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

if "current_user" not in st.session_state:
    st.session_state.current_user = "IRENE"

# --- 1. 頁面設定 ---
st.set_page_config(page_title="CAL Crew Calendar", page_icon="📅", layout="wide")

BG_BLACK = "#0E0E0E"
IRENE_PINK = "#F07699" # 妳最愛的粉紅

# --- 2. 四人班表資料庫 ---
USERS_DATA = {
    "IRENE": {
        "color": IRENE_PINK,
        "roster": {
            "2026-04-03": "116", "2026-04-05": "517", "2026-04-08": "108",
            "2026-04-10": "915", "2026-04-12": "150", "2026-04-13": "151",
            "2026-04-14": "130", "2026-04-15": "131", "2026-04-30": "156"
        }
    },
    "ISABELLE": { "color": "#A28CF0", "roster": {"2026-04-03": "108", "2026-04-12": "116"} },
    "小米": { "color": "#76C9F0", "roster": {"2026-04-05": "116", "2026-04-14": "527"} },
    "大飄": { "color": "#F0B476", "roster": {"2026-04-04": "150", "2026-04-16": "517"} }
}

# --- 3. 強制粉紅 CSS 鎖定 ---
user_color = USERS_DATA[st.session_state.current_user]["color"]

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 暴力鎖死：月曆格子底色與大白字 */
    .fc-event, .fc-event-main {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        background: {user_color} !important;
    }}
    
    .fc-event-title {{
        font-size: 2.2em !important; /* 數字維持最大 */
        font-weight: 900 !important;
        color: white !important;
        text-align: center !important;
    }}

    [data-testid="stSidebar"] {{
        background-color: #151515;
        border-right: 2px solid {user_color};
    }}
    
    .report-card {{
        background: #1F1F1F; border-radius: 15px; padding: 25px;
        border: 2px solid {user_color}; margin-bottom: 15px;
        box-shadow: 0 0 15px {user_color}44;
    }}
    
    .tag {{ background: {user_color}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; }}

    div.stButton > button {{
        background-color: #222; color: white; border: 1px solid #444;
        font-weight: 800; width: 100%; height: 3.5em; border-radius: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 4. 側邊欄導航 ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{user_color}; text-align:center;'>✈️ CREW MENU</h2>", unsafe_allow_html=True)
    
    for name in USERS_DATA.keys():
        label = f"🌸 {name}" if st.session_state.current_user == name else f"👤 {name}"
        if st.button(label, key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
            
    st.divider()
    if st.button(f"📍 TODAY ({today_str})"):
        st.session_state.sel_f = USERS_DATA[st.session_state.current_user]["roster"].get(today_str, "None")
    
    st.divider()
    st.subheader("📋 Flight Details")
    details_placeholder = st.empty()

# --- 5. 主頁面月曆 ---
current_user = st.session_state.current_user
user_info = USERS_DATA[current_user]
calendar_events = [{"title": f, "start": d, "end": d, "allDay": True} for d, f in user_info["roster"].items()]

st.title(f"💖 {current_user}'S CALENDAR")

calendar_options = {
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
    "initialView": "dayGridMonth",
    "initialDate": today_str,
    "contentHeight": "auto",
}
state = calendar(events=calendar_events, options=calendar_options, key=f"cal_{current_user}")

# --- 6. 詳情顯示 ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['班號'] = df['班號'].astype(str).str.replace('CI', '').str.strip()
    
    target = None
    if state.get("eventClick"):
        target = state["eventClick"]["event"]["title"].strip()
    elif "sel_f" in st.session_state:
        target = st.session_state.sel_f

    with details_placeholder.container():
        if target and target != "None":
            stay_list = ["150", "151", "130", "131", "731", "732"]
            s_list = [target]
            if target not in stay_list:
                try: s_list.append(str(int(target) + 1))
                except: pass
                
            for t in s_list:
                match = df[df['班號'] == t]
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
            st.info("今天放假！休息愉快 ☕")
        else:
            st.write("✨ 點擊班號查看詳情")
except Exception as e:
    st.sidebar.error("CSV 資料讀取有誤")
