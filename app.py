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
    st.session_state.current_user = "Irene"

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL SCHEDULE", page_icon="✈️", layout="wide")

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    
    /* 🚀 暴力鎖死：去藍變粉，背景與邊框全部強制換色 */
    .fc-event, .fc-event-main, .fc-daygrid-event, .fc-v-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        background: {user_color} !important;
    }}
    
    /* 🚀 白色大粗體班號：2.0em */
    .fc-event-title {{
        font-size: 2.0em !important; 
        font-weight: 900 !important; 
        text-align: center !important; 
        color: white !important;
        display: block !important;
    }}

    .fc-daygrid-event-harness {{ min-height: 65px !important; }}

    .report-card {{
        background: #1A1A1A; border-radius: 15px; padding: 20px;
        border: 2px solid {user_color}; box-shadow: 0 0 15px rgba(240,118,153,0.2);
        margin-top: 10px;
    }}
    .tag {{
        background: {user_color}; color: white; padding: 3px 10px;
        border-radius: 5px; font-size: 0.8rem; font-weight: 900;
    }}

    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.2em;
        font-size: 1rem; transition: 0.2s; margin-bottom: 5px;
    }}
    div.stButton > button:hover {{ border-color: {user_color}; color: {user_color} !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊導覽列 (SCHEDULE) ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:{user_color};'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    st.write("---")
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    st.subheader("📋 Flight Details")
    info_area = st.empty()

# --- 3. 數據讀取 ---
calendar_events = []
flight_db = pd.DataFrame()

try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        calendar_events.append({
            "title": str(row['班號']), "start": clean_date, "end": clean_date, "allDay": True
        })
except Exception as e:
    info_area.error(f"讀取 {st.session_state.current_user} 班表失敗")

# --- 4. 主月曆 ---
st.title(f"💖 {st.session_state.current_user}'s Roster")

calendar_options = {
    "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
    "initialDate": today_str,
    "contentHeight": 700,
    "displayEventTime": False,
    "dayMaxEvents": False
}

state = calendar(events=calendar_events, options=calendar_options, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示邏輯 (修復自動找回程功能) ---
if state.get("eventClick"):
    fno = state["eventClick"]["event"]["title"].strip()
    
    # ✈️ 過夜班名單 (手動加入不需要自動抓 +1 的班號)
    stay_only_flights = ["150", "130", "731", "721"] 
    
    search_list = [fno]
    # 如果是偶數班號且非純過夜班，自動抓回程 (+1)
    if fno not in stay_only_flights:
        try:
            if int(fno) % 2 == 0:
                search_list.append(str(int(fno) + 1))
        except: pass

    with info_area.container():
        for t in search_list:
            match = flight_db[flight_db['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                # 判定顯示標籤
                tag = "GO" if (len(search_list) > 1 and t == fno) else ("RTN" if len(search_list) > 1 else "STAY")
                
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{user_color}; margin:0;'>CI {t}</h2>
                            <span class="tag">{tag}</span>
                        </div>
                        <p style='margin:10px 0; font-size:1.3rem; font-weight:800;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.1rem; margin:5px 0;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:10px 0;'>
                        <p style='font-size:0.9rem; color:#AAA; margin:0;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
            elif t == fno:
                st.warning(f"找不到班號 {t} 的詳細資訊")
else:
    info_area.write("✨ 點擊月曆班號看詳情")
