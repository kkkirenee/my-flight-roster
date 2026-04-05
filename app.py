import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 初始化 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

if "current_user" not in st.session_state:
    st.session_state.current_user = "IRENE"

# --- 1. 成員配置 (對應 Excel 的分頁名稱) ---
CREW_CONFIG = {
    "IRENE": {"color": "#F07699", "icon": "🌸"},
    "ISABELLE": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}

user_color = CREW_CONFIG[st.session_state.current_user]["color"]
st.set_page_config(page_title="CAL Crew Hub", page_icon="✈️", layout="wide")

# --- 2. CSS 樣式 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    .fc-event {{ background-color: {user_color} !important; border-color: {user_color} !important; }}
    .fc-event-title {{ font-size: 2.0em !important; font-weight: 900 !important; color: white !important; text-align: center !important; }}
    .report-card {{ background: #1F1F1F; border-radius: 15px; padding: 22px; border: 2px solid {user_color}; margin-bottom: 15px; }}
    .tag {{ background: {user_color}; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 800; }}
    div.stButton > button {{ background-color: #262626; color: white; border: 1px solid #444; font-weight: 800; width: 100%; height: 3.5em; border-radius: 10px; }}
    </style>
    """, unsafe_allow_html=True)

# --- 3. 數據讀取 (核心：指定讀取 Excel 的 Sheet) ---
calendar_events = []
try:
    # 讀取航班詳情字典
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 💡 讀取 Excel 的指定分頁
    # 這裡的 sheet_name 會跟著左邊按鈕的名字變動
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        calendar_events.append({
            "title": str(row['班號']),
            "start": str(row['日期']).split()[0], # 確保拿到的只有日期字串
            "end": str(row['日期']).split()[0],
            "allDay": True
        })
except Exception as e:
    st.sidebar.warning(f"✨ 尚未在 Excel 中找到 {st.session_state.current_user} 的分頁數據")

# --- 4. 介面與月曆 ---
with st.sidebar:
    st.markdown(f"<h2 style='color:{user_color}; text-align:center;'>✈️ CREW MENU</h2>", unsafe_allow_html=True)
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    st.subheader("📋 Flight Details")
    details_placeholder = st.empty()

st.title(f"💖 {st.session_state.current_user}'S CALENDAR")
state = calendar(events=calendar_events, options={"initialDate": today_str, "contentHeight": "auto"}, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示 ---
overnight_flights = ["130", "731", "150", "761", "721", "771"]
target = None
if state.get("eventClick"):
    target = state["eventClick"]["event"]["title"].strip()

with details_placeholder.container():
    if target:
        s_list = [target]
        if target not in overnight_flights:
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
                        <p style='margin:10px 0 5px 0; font-size:1.4rem; font-weight:700;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.1rem;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:15px 0;'>
                        <p style='margin:0; font-size:1rem; color:#AAA;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
