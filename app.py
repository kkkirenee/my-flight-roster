import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import re

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL SCHEDULE", page_icon="✈️", layout="wide")
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

# 成員配色
CREW_CONFIG = {
    "Irene": {"color": "#F07699", "icon": "🌸"},
    "Isabelle": {"color": "#A28CF0", "icon": "👤"},
    "小米": {"color": "#76C9F0", "icon": "👤"},
    "大飄": {"color": "#F0B476", "icon": "👤"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 極簡風格鎖定 ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #0E0E0E; color: white; }}
    [data-testid="stSidebar"] {{ background-color: #151515; border-right: 2px solid {user_color}; }}
    .flight-box {{
        background-color: {user_color};
        color: white;
        padding: 10px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
        cursor: pointer;
    }}
    .flight-num {{ font-size: 2.5rem !important; font-weight: 900; line-height: 1; }}
    .detail-card {{
        background: #1A1A1A; border: 2px solid {user_color};
        padding: 15px; border-radius: 15px; margin-bottom: 10px;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 側邊欄 (SCHEDULE) ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align:center; color:{user_color};'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    st.divider()
    for name in CREW_CONFIG.keys():
        if st.button(f"{CREW_CONFIG[name]['icon']} {name}", key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    st.subheader("📋 Flight Details")
    info_placeholder = st.empty()

# --- 3. 數據讀取 ---
try:
    # 航班字典
    df_flight = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df_flight.columns = df_flight.columns.str.strip()
    df_flight['班號'] = df_flight['班號'].astype(str).str.replace('CI', '').str.strip()
    
    # 個人班表
    df_roster = pd.read_excel('CAL_Roster.xlsx', sheet_name=st.session_state.current_user)
    df_roster.columns = df_roster.columns.str.strip()
    # 建立日期索引字典
    roster_dict = {}
    for _, row in df_roster.iterrows():
        d = row['日期'].strftime('%Y-%m-%d') if isinstance(row['日期'], datetime) else str(row['日期']).split()[0]
        roster_dict[d] = str(row['班號'])
except:
    st.sidebar.error("資料讀取失敗，請檢查檔案與分頁名稱")

# --- 4. 主畫面：改用原生 Columns 製作「真‧大字月曆」 ---
st.title(f"💖 {st.session_state.current_user}'s Roster")

# 這裡我們用 Python 的方式來畫月曆，保證字體大小受控
import calendar
curr_month = now_tw.month
curr_year = now_tw.year
month_name = calendar.month_name[curr_month]
st.subheader(f"📅 {month_name} {curr_year}")

cols = st.columns(7)
weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
for i, day in enumerate(weekdays):
    cols[i].markdown(f"<p style='text-align:center; color:#888;'>{day}</p>", unsafe_allow_html=True)

cal = calendar.Calendar(firstweekday=0)
month_days = cal.monthdayscalendar(curr_year, curr_month)

for week in month_days:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write("")
        else:
            date_str = f"{curr_year}-{curr_month:02d}-{day:02d}"
            flight_val = roster_dict.get(date_str, "")
            
            # 格子容器
            with cols[i].container():
                st.markdown(f"<p style='margin:0; color:#555;'>{day}</p>", unsafe_allow_html=True)
                if flight_val:
                    # 🚀 這裡就是妳要的：超級大字、粉紅色背景
                    if st.button(flight_val, key=f"date_{day}"):
                        st.session_state.selected_flight = flight_val
                    st.markdown(f"""
                        <div style='background:{user_color}; border-radius:8px; padding:5px; text-align:center; margin-top:-35px; pointer-events:none;'>
                            <span style='font-size:1.8rem; font-weight:900; color:white;'>{flight_val}</span>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.write("")

# --- 5. 詳情顯示 ---
selected = st.session_state.get("selected_flight")
if selected:
    fnos = re.findall(r'\d+', selected)
    with info_placeholder.container():
        for f in fnos:
            m = df_flight[df_flight['班號'] == f]
            if not m.empty:
                r = m.iloc[0]
                st.markdown(f"""
                    <div class="detail-card">
                        <h2 style='color:{user_color}; margin:0;'>CI {f}</h2>
                        <p style='font-size:1.2rem; font-weight:700; margin:10px 0;'>📍 {r['目的地']}</p>
                        <p>⏰ 報到: {r.get('報到時間','--:--')}</p>
                        <p style='font-size:0.9rem; color:#888;'>🛫 {r.get('起飛時間','--:--')} | 🛬 {r.get('落地時間','--:--')}</p>
                    </div>
                """, unsafe_allow_html=True)
