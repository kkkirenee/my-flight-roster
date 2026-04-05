import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime
import pytz

# --- 0. 初始化設定 ---
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

# --- 1. 頁面風格與成員配置 ---
st.set_page_config(page_title="CAL Crew Hub", page_icon="✈️", layout="wide")

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}

if st.session_state.current_user not in CREW_CONFIG:
    st.session_state.current_user = "Irene"

user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# 🎨 視覺強化：超級粉紅大字 CSS
st.markdown(f"""
    <style>
    /* 背景與基礎文字 */
    .stApp {{ background-color: #0E0E0E; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 3px solid {user_color}; }}
    
    /* 標題大字 */
    h1 {{ 
        font-size: 3.5rem !important; 
        color: {user_color} !important; 
        font-weight: 900 !important;
        text-shadow: 2px 2px 10px {user_color}66;
    }}
    
    /* 月曆內部的班號大字 */
    .fc-event {{ 
        background-color: {user_color} !important; 
        border: none !important; 
        border-radius: 8px !important;
        padding: 5px !important;
    }}
    .fc-event-title {{ 
        font-size: 2.2rem !important; /* 班號變超級大 */
        font-weight: 900 !important; 
        color: white !important; 
        text-align: center !important; 
    }}
    
    /* 側邊欄按鈕大字 */
    div.stButton > button {{ 
        background-color: #262626; 
        color: white !important; 
        border: 2px solid #444; 
        font-size: 1.5rem !important; /* 按鈕名字變大 */
        font-weight: 800 !important; 
        width: 100%; 
        height: 4em; 
        border-radius: 15px;
        margin-bottom: 10px;
        transition: 0.3s;
    }}
    div.stButton > button:hover {{
        border-color: {user_color};
        color: {user_color} !important;
        box-shadow: 0 0 15px {user_color}66;
    }}
    
    /* 航班詳情卡片 */
    .report-card {{ 
        background: #1F1F1F; border-radius: 20px; padding: 25px; 
        border: 3px solid {user_color}; margin-bottom: 20px; 
    }}
    .tag {{ background: {user_color}; color: white; padding: 5px 15px; border-radius: 8px; font-weight: 900; font-size: 1.1rem; }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 數據讀取邏輯 ---
calendar_events = []
try:
    flight_db = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    flight_db.columns = flight_db.columns.str.strip()
    flight_db['班號'] = flight_db['班號'].astype(str).str.replace('CI', '').str.strip()
    
    user_df = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    user_df.columns = user_df.columns.str.strip()
    
    for _, row in user_df.iterrows():
        raw_date = row['日期']
        if isinstance(raw_date, datetime):
            clean_date = raw_date.strftime('%Y-%m-%d')
        else:
            clean_date = str(raw_date).split()[0]
            
        calendar_events.append({
            "title": str(row['班號']),
            "start": clean_date,
            "end": clean_date,
            "allDay": True
        })
except Exception as e:
    st.sidebar.warning(f"✨ 尚未在 Excel 中找到 {st.session_state.current_user} 的分頁")

# --- 3. 側邊欄導航 ---
with st.sidebar:
    st.markdown(f"<h1 style='font-size:2rem !important; text-align:center;'>✈️ MENU</h1>", unsafe_allow_html=True)
    for name, config in CREW_CONFIG.items():
        if st.button(f"{config['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    st.subheader("📋 Flight Details")
    details_placeholder = st.empty()

# --- 4. 主頁面月曆 ---
st.title(f"💖 {st.session_state.current_user}")
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
                            <h2 style='color:{user_color}; margin:0; font-size:2.5rem;'>CI {t}</h2>
                            <span class="tag">{tag}</span>
                        </div>
                        <p style='margin:15px 0 5px 0; font-size:1.8rem; font-weight:800;'>📍 {r['目的地']}</p>
                        <p style='font-size:1.3rem;'>⏰ 報到: <span style='color:{user_color}; font-weight:900;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:20px 0;'>
                        <p style='margin:0; font-size:1.1rem; color:#AAA;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.write("✨ 點擊班號查看大圖詳情")
