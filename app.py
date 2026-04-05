import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import re
import os

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL SCHEDULE", layout="wide")

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "sheet": "Irene"},
    "Isabelle": {"color": "#A28CF0", "sheet": "Isabelle"},
    "Elaine": {"color": "#76C9F0", "sheet": "Elaine"},
    "Bigpiao": {"color": "#F0B476", "sheet": "Bigpiao"}
}

if "current_user" not in st.session_state:
    st.session_state.current_user = "Elaine"

user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 視覺風格 (🚀 版面往上移 + 修正 Today 點擊) ---
st.markdown(f"""
    <style>
    /* 🚀 砍掉頂部空白，讓版面往上移 */
    .stApp {{ background-color: #0E0E0E; color: white; }}
    .block-container {{ padding-top: 1rem !important; padding-bottom: 0rem !important; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 🚀 姓名按鈕 - 維持精緻長方形 */
    .stButton > button {{
        width: 100% !important; height: 50px !important;
        font-size: 1.2rem !important; font-weight: 800 !important;
        color: white !important; background-color: #1A1A1A !important;
        border-radius: 12px !important; border: 2px solid transparent !important; 
        background: linear-gradient(#1A1A1A, #1A1A1A) padding-box,
                    linear-gradient(135deg, {user_color}88, #0E0E0E) border-box !important;
        margin-bottom: 10px !important;
    }}

    /* 🚀 月曆 Header 優化與 Today 功能恢復 */
    .fc .fc-toolbar {{ margin-bottom: 1em !important; }}
    
    /* 解決 Today 不能按 & 紅色按鈕問題 */
    .fc .fc-button {{
        background-color: transparent !important;
        background-image: none !important;
        border: 2px solid {user_color} !important;
        color: {user_color} !important;
        font-weight: 800 !important;
        opacity: 1 !important;
        cursor: pointer !important;
        pointer-events: auto !important;
    }}
    .fc .fc-button:hover {{
        background-color: {user_color}33 !important;
        color: white !important;
    }}
    .fc .fc-button-active, .fc .fc-button:active {{
        background-color: {user_color} !important;
        color: white !important;
    }}

    /* 月曆字體維持 1.8em */
    div.fc-event {{ background-color: {user_color} !important; border: none !important; }}
    .fc-event-title {{ font-size: 1.8em !important; font-weight: 900 !important; }}

    /* 航班資訊卡片 */
    .flight-card {{
        background: #1A1A1A; border-radius: 20px; padding: 20px !important;
        border: 3px solid {user_color} !important; margin-top: 10px;
    }}
    .card-title {{ color: {user_color}; font-size: 1.5rem !important; font-weight: 900; }}
    </style>

    <script>
    // 🚀 暴力 JavaScript：只要點不到，我就幫你點
    document.addEventListener('click', function(e) {{
        const target = e.target;
        if (target.classList.contains('fc-today-button')) {{
            console.log('Today clicked via JS');
            // 這裡可以強制觸發月曆回今天，但一般來說 pointer-events:auto 就夠了
        }}
    }}, true);
    </script>
    """, unsafe_allow_html=True)

# --- 2. 側邊欄 ---
with st.sidebar:
    st.markdown(f"<h1 style='color:{user_color}; font-weight:900; text-align:center; margin-bottom:15px;'>✈️ SCHEDULE</h1>", unsafe_allow_html=True)
    for name in CREW_CONFIG.keys():
        if st.button(name, key=f"btn_{name}"):
            st.session_state.current_user = name
            st.rerun()
    st.divider()
    info_placeholder = st.container()

# --- 3. 數據解析 (維持邏輯) ---
calendar_events = []
flight_db = pd.DataFrame()
click_lookup = {} 
try:
    if os.path.exists("my_flights.csv"):
        flight_db = pd.read_csv("my_flights.csv", encoding='utf-8-sig').fillna("")
        flight_db.columns = flight_db.columns.str.strip()
        flight_db['f_clean'] = flight_db['班號'].astype(str).str.upper().str.replace('CI', '').str.strip()
    xl = pd.ExcelFile("CAL_Roster.xlsx")
    df = pd.read_excel(xl, sheet_name=CREW_CONFIG[st.session_state.current_user]["sheet"])
    df.columns = df.columns.str.strip()
    for _, row in df.iterrows():
        if pd.isna(row['日期']): continue
        start_dt = pd.to_datetime(row['日期'])
        f_no = str(row['班號']).strip()
        memo = str(row.get('備註', '')).strip()
        d_key = start_dt.strftime('%Y-%m-%d')
        flight_list = [f_no]
        rtn_fno = ""
        date_pattern = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', memo)
        rtn_match = re.search(r'回程\s*(\d+)', memo)
        if rtn_match:
            rtn_fno = rtn_match.group(1)
            if not date_pattern: flight_list.append(rtn_fno)
        click_lookup[d_key] = {"flights": flight_list, "memo": memo}
        calendar_events.append({"title": f_no, "start": d_key, "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
        if date_pattern:
            try:
                end_dt = pd.to_datetime(date_pattern.group(1))
                if end_dt > start_dt:
                    if (end_dt - start_dt).days > 1:
                        calendar_events.append({"title": " ", "start": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "end": end_dt.strftime('%Y-%m-%d'), "allDay": True})
                    r_key = end_dt.strftime('%Y-%m-%d')
                    click_lookup[r_key] = {"flights": [rtn_fno], "memo": f"回程自 {start_dt.strftime('%m/%d')} CI{f_no}"}
                    calendar_events.append({"title": rtn_fno, "start": r_key, "end": (end_dt + timedelta(days=1)).strftime('%Y-%m-%d'), "allDay": True})
            except: pass
except Exception as e:
    st.sidebar.error(f"錯誤：{e}")

# --- 4. 渲染月曆 (🚀 鎖死 Today 權限 + 緊湊版面) ---
st.markdown(f"<h2 style='margin-bottom:0px;'>💖 {st.session_state.current_user}</h2>", unsafe_allow_html=True)
cal_css = f"""
    .fc-event-main {{ background-color: {user_color} !important; }}
    .fc-event-title {{ font-size: 1.8em !important; font-weight: 900 !important; }}
    .fc .fc-button-primary {{ border: 2px solid {user_color} !important; color: {user_color} !important; pointer-events: auto !important; cursor: pointer !important; }}
"""
state = calendar(
    events=calendar_events, 
    options={"initialDate": "2026-04-01", "displayEventTime": False, "headerToolbar": {"left": "prev,next today", "center": "title", "right": ""}}, 
    custom_css=cal_css,
    key=f"cal_vfinal_top_{st.session_state.current_user}"
)

# --- 5. 點擊顯示 ---
if state.get("eventClick"):
    clicked_date = state["eventClick"]["event"]["start"].split('T')[0]
    info = click_lookup.get(clicked_date)
    if info:
        with info_placeholder:
            for fno in info["flights"]:
                target_f = fno.upper().replace('CI', '').strip()
                match = flight_db[flight_db['f_clean'] == target_f] if not flight_db.empty else pd.DataFrame()
                if not match.empty:
                    r = match.iloc[0]
                    def get_v(keys):
                        for k in keys:
                            if k in r and str(r[k]).strip() != "": return str(r[k]).strip()
                        return "--:--"
                    dest = get_v(['目的地', '地點'])
                    report = get_v(['報到時間', '報到'])
                    dep_t = get_v(['起飛時間', '起飛'])
                    arr_t = get_v(['落地時間', '降落時間', '降落', 'ARR'])
                    st.markdown(f"""
                        <div class="flight-card">
                            <p class="card-title">CI {target_f}</p>
                            <p style="font-size:1.8rem; font-weight:950; margin:5px 0;">📍 {dest}</p>
                            <p style="font-size:1rem; color:#BBB; margin-bottom:5px;">⏰ 報到時間: {report}</p>
                            <div class="time-box">
                                <div style="text-align:center;"><p style="font-size:0.8rem; color:#888; margin:0;">起飛 DEP</p><p style="font-size:1.4rem; font-weight:800; color:white; margin:0;">{dep_t}</p></div>
                                <div style="align-self:center; color:#555;">✈️</div>
                                <div style="text-align:center;"><p style="font-size:0.8rem; color:#888; margin:0;">落地 ARR</p><p style="font-size:1.4rem; font-weight:800; color:white; margin:0;">{arr_t}</p></div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
