import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL Crew Hub", page_icon="✈️", layout="wide")
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

CREW_CONFIG = {import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 基本設定 ---
st.set_page_config(page_title="小隊班表", page_icon="✈️", layout="wide")
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "🌸"},
    "小米": {"color": "#76C9F0", "icon": "🌸"},
    "大飄": {"color": "#F0B476", "icon": "🌸"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺鎖定 CSS ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 去藍變粉：鎖定所有層級 */
    .fc-event, .fc-event-main, .fc-daygrid-event {{
        background-color: {user_color} !important;
        border: none !important;
    }}

    /* 🚀 字體絕對放大：針對班號 116 等數字 */
    .fc-event-title {{
        font-size: 2.8rem !important; 
        font-weight: 900 !important;
        line-height: 1.1 !important;
        text-align: center !important;
        display: block !important;
        padding: 20px 0 !important;
    }}

    /* 讓月曆格子有足夠高度顯示大字 */
    .fc-daygrid-event-harness {{ min-height: 60px !important; }}
    
    /* 詳情資訊卡片：確保它是亮的、大的、看得到的 */
    .detail-card {{
        background: #1F1F1F;
        padding: 20px;
        border-radius: 15px;
        border: 3px solid {user_color};
        margin-top: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
calendar_events = []
try:
    # 讀取航班字典
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 讀取 Excel 分頁
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        
        calendar_events.append({
            "title": str(row['班號']),
            "start": clean_date,
            "end": clean_date,
            "allDay": True,
            "backgroundColor": user_color,
            "borderColor": user_color,
        })
except Exception as e:
    st.sidebar.warning(f"尚未找到 {st.session_state.current_user} 的資料")

# --- 3. 側邊導航 ---
with st.sidebar:
    st.markdown(f"### ✈️ Menu")
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    st.subheader("📋 航班詳情")
    # 🚀 這裡是最重要的地方：詳情預留位
    details_container = st.container()

# --- 4. 主月曆 ---
st.title(f"💖 {st.session_state.current_user}")

state = calendar(
    events=calendar_events, 
    options={
        "initialDate": today_str,
        "contentHeight": 650,
        "dayMaxEvents": False,
    }, 
    key=f"cal_{st.session_state.current_user}"
)

# --- 5. 詳情顯示邏輯 (修復消失問題) ---
if state.get("eventClick"):
    # 抓取點擊的班號
    clicked_fno = state["eventClick"]["event"]["title"].strip()
    
    # 在側邊欄容器顯示資訊
    with details_container:
        match = flight_db[flight_db['班號'] == clicked_fno]
        if not match.empty:
            r = match.iloc[0]
            st.markdown(f"""
                <div class="detail-card">
                    <h2 style='color:{user_color}; margin:0;'>CI {clicked_fno}</h2>
                    <p style='font-size:1.5rem; font-weight:800; margin:10px 0;'>📍 {r['目的地']}</p>
                    <p style='font-size:1.1rem;'>⏰ 報到: {r.get('報到時間','--:--')}</p>
                    <p style='font-size:0.9rem; color:#AAA;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info(f"找不到班號 {clicked_fno} 的詳細資訊")
else:
    with details_container:
        st.write("✨ 點擊班號看詳情")
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 暴力字體 CSS (精準鎖定) ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    
    /* 🚀 移除所有藍色，強制粉紅背景 */
    .fc-event, .fc-event-main, .fc-daygrid-event {{
        background-color: {user_color} !important;
        background: {user_color} !important;
        border: none !important;
    }}

    /* 🚀 核心：精準放大 116 這種班號字體 */
    .fc-event-title {{
        font-size: 3.2rem !important; /* 超級巨無霸字體 */
        font-weight: 900 !important;
        color: white !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        height: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
    }}

    /* 讓班號容器充滿格子，不留空白 */
    .fc-event-main {{
        padding: 0 !important;
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
    }}

    /* 格子高度稍微調回正常，但要足夠裝下大字 */
    .fc-daygrid-event-harness {{ 
        height: 55px !important; 
        margin: 2px 0 !important; 
    }}
    
    /* 姓名按鈕回歸正常小小的 */
    div.stButton > button {{ font-size: 0.9rem !important; height: 2.2em !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取 ---
calendar_events = []
try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 讀取 Excel (分頁 Irene / Isabelle)
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        clean_date = raw_date.strftime('%Y-%m-%d') if isinstance(raw_date, datetime) else str(raw_date).split()[0]
        
        calendar_events.append({
            "title": str(row['班號']),
            "start": clean_date,
            "end": clean_date,
            "allDay": True,
            "backgroundColor": user_color,
            "borderColor": user_color,
            "display": "block"
        })
except Exception as e:
    st.sidebar.warning(f"尚未找到 {st.session_state.current_user} 的資料")

# --- 3. 介面呈現 ---
with st.sidebar:
    st.markdown(f"### ✈️ Menu")
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    details_placeholder = st.empty()

st.title(f"💖 {st.session_state.current_user}")

state = calendar(
    events=calendar_events, 
    options={
        "initialDate": today_str,
        "contentHeight": "auto",
        "displayEventTime": False,
        "dayMaxEvents": False, # 不縮減，全部顯示
    }, 
    key=f"cal_{st.session_state.current_user}"
)

# --- 4. 詳情顯示 ---
if state.get("eventClick"):
    t = state["eventClick"]["event"]["title"].strip()
    match = flight_db[flight_db['班號'] == t]
    if not match.empty:
        r = match.iloc[0]
        with details_placeholder.container():
            st.markdown(f"""
                <div style='background:#1F1F1F; padding:15px; border-radius:10px; border:2px solid {user_color};'>
                    <h2 style='color:{user_color};'>CI {t}</h2>
                    <p style='font-size:1.2rem; font-weight:700;'>📍 {r['目的地']}</p>
                </div>
            """, unsafe_allow_html=True)
