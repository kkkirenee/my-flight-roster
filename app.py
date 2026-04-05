import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 時區與初始化 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

# 紀錄目前是誰的班表
if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL SCHEDULE", page_icon="✈️", layout="wide")

# 成員顏色配置
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
    
    /* 🚀 強制鎖死月曆內部的顏色，防止藍色出現 */
    .fc-event {{
        background-color: {user_color} !important;
        border-color: {user_color} !important;
        color: white !important;
        background: {user_color} !important;
    }}
    
    .report-card {{
        background: #1A1A1A; border-radius: 20px; padding: 25px;
        border: 2px solid {user_color}; box-shadow: 0 0 20px rgba(240,118,153,0.3);
        margin-bottom: 15px;
    }}
    .tag {{
        background: {user_color}; color: white; padding: 4px 12px;
        border-radius: 6px; font-size: 0.9rem; font-weight: 900;
    }}
    /* 側邊欄按鈕樣式 */
    div.stButton > button {{
        background-color: #262626; color: white; border: 1px solid #444;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
        font-size: 1.1rem; transition: 0.3s; margin-bottom: 10px;
    }}
    div.stButton > button:hover {{
        border-color: {user_color}; color: {user_color} !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊導航列 (SCHEDULE) ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:{user_color}; font-weight:900;'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    st.divider()
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    st.subheader("📋 Flight Details")
    info_area = st.empty()

# --- 3. 數據讀取 (核心：連動 Excel 分頁) ---
calendar_events = []
flight_db = pd.DataFrame()
try:
    # 讀取航班字典
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 🚀 根據點選的名字讀取對應的 Excel 分頁
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        calendar_events.append({
            "title": str(row['班號']), "start": clean_date, "end": clean_date,
            "backgroundColor": user_color, "borderColor": user_color, "allDay": True
        })
except Exception as e:
    st.sidebar.error(f"找不到 {st.session_state.current_user} 的班表資料")

# --- 4. 顯示介面 ---
st.title(f"💖 {st.session_state.current_user}'s Roster")

col1, col2 = st.columns([2.5, 0.1]) # 主要畫面放在左邊大區塊

with col1:
    calendar_options = {
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "initialDate": today_str,
        "contentHeight": "auto",
        "displayEventTime": False,
        "dayMaxEvents": False
    }
    # 🚀 這裡就是妳最滿意的大字 CSS
    custom_css = ".fc-event-title { font-size: 1.8em !important; font-weight: 900 !important; text-align: center !important; color: white !important; }"
    state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key=f"cal_{st.session_state.current_user}")

# --- 5. 詳情顯示邏輯 (包含自動回程連動) ---
if state.get("eventClick"):
    fno = state["eventClick"]["event"]["title"].strip()
    
    # 🚀 這裡是之前的回程邏輯，我把它完整加回來了
    stay_list = ["150", "151", "130", "131", "731", "732"]
    search_list = [fno]
    if fno not in stay_list:
        try:
            if int(fno) % 2 == 0: # 雙數找 +1
                search_list.append(str(int(fno) + 1))
        except: pass

    with info_area.container():
        for t in search_list:
            match = flight_db[flight_db['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                tag = "GO" if (len(search_list)>1 and t==fno) else ("RTN" if len(search_list)>1 else "STAY")
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{user_color}; margin:0;'>CI {t}</h2>
                            <span class="tag">{tag}</span>
                        </div>
                        <p style='margin:10px 0; font-size:1.2rem; font-weight:800;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.1rem;'>⏰ 報到: <span style='color:{user_color}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:10px 0;'>
                        <p style='font-size:0.9rem; color:#AAA; margin:0;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
else:
    info_area.write("✨ 點擊班號看詳情")
