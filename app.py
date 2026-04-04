import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import pytz

# --- 0. 時區校準 (台灣時區) ---
# 強制抓取台北時間，避免伺服器時差導致 5 號變成 4 號
tw_tz = pytz.timezone('Asia/Taipei')
now_tw = datetime.now(tw_tz)
today_str = now_tw.strftime("%Y-%m-%d")

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL Calendar", page_icon="📅", layout="wide")

# ✨ 關鍵修改：選用更淡、更暖、更柔和的粉紅色 (Sakura Pink)
WARM_PINK = "#FFB7C5"
BG_BLACK = "#0E0E0E"
CARD_BG = "#1A1A1A" # 卡片背景稍微亮一點點，增加層次

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    
    /* 詳情卡片 (Details Card) */
    .report-card {{
        background: {CARD_BG}; 
        border-radius: 20px; 
        padding: 25px;
        border: 2px solid {WARM_PINK}; 
        box-shadow: 0 0 25px rgba(255,183,197,0.25); /* 柔和的發光 */
        margin-bottom: 15px;
        transition: 0.3s;
    /* 去程標籤 (GO Tag) */
    .tag-go {{
        background: {WARM_PINK}; color: #333; /* 暗色文字增加對比 */
        padding: 4px 12px; border-radius: 6px; 
        font-size: 0.9rem; font-weight: 900;
    }}
    
    /* 自定義 Today 大按鈕樣式 (使用暖粉色) */
    div.stButton > button {{
        background-color: {WARM_PINK}; color: #333; border: none;
        font-weight: 900; width: 100%; border-radius: 12px; height: 3.5em;
        font-size: 1.1rem; transition: 0.3s;
        box-shadow: 0 4px 15px rgba(255,183,197,0.3);
    }}
    div.stButton > button:hover {{
        background-color: #ffc8d5; /* 滑過時更淡一點 */
        transform: scale(1.02);
    }}
    
    /* 月曆內部樣式 */
    .fc-event-title {{ 
        font-size: 1.5em !important; /* 字體維持最大 */
        font-weight: 900 !important; 
        color: #333 !important; /* 數字改成暗色，配暖粉背景 */
    }}
    .fc-dayGridMonth-view .fc-event {{
        background-color: {WARM_PINK} !important;
        border-color: {WARM_PINK} !important;
        border-radius: 6px !important;
        padding: 4px 0 !important;
    }}
    .fc .fc-button-primary {{
        background-color: {CARD_BG} !important;
        border-color: {WARM_PINK} !important;
        color: {WARM_PINK} !important;
        text-transform: capitalize !important;
    }}
    .fc .fc-button-primary:hover {{
        background-color: {WARM_PINK} !important;
        color: #333 !important;
    }}
    .fc .fc-day-today {{
        background: rgba(255, 183, 197, 0.15) !important; /* 今天格子的柔和背景 */
    }}
    .fc-col-header-cell-cushion {{
        color: #AAA !important; /* 星期文字改成淺灰 */
    }}
    </style>
    """, unsafe_allow_html=True)

# --- 2. 班表資料 ---
ROSTER = {
    "2026-04-03": "116", "2026-04-05": "517", "2026-04-08": "108",
    "2026-04-10": "915", "2026-04-12": "150", "2026-04-13": "151",
    "2026-04-14": "130", "2026-04-15": "131", "2026-04-16": "527", 
    "2026-04-18": "731", "2026-04-19": "732", "2026-04-21": "186", 
    "2026-04-23": "783", "2026-04-25": "190", "2026-04-30": "156"
}

calendar_events = []
for date_key, flight in ROSTER.items():
    calendar_events.append({
        "title": flight, "start": date_key, "end": date_key,
    })

# --- 3. 讀取 CSV ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    # 統一將班號欄位處理乾淨
    df['班號'] = df['班號'].astype(str).str.replace('CI', '').str.strip()
except:
    st.error("找不到 CSV 資料")
    st.stop()

# --- 4. 顯示介面 ---
st.title("💖 FLIGHT CALENDAR")

# 大按鈕上的日期自動更新 (2026-04-05)
if st.button(f"📍 SHOW TODAY'S FLIGHT ({today_str})"):
    if today_str in ROSTER:
        st.session_state.selected_f = ROSTER[today_str]
    else:
        st.session_state.selected_f = "None"

col1, col2 = st.columns([2.5, 1])

with col1:
    calendar_options = {
        "headerToolbar": {"left": "prev,next", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "initialDate": today_str,
        "contentHeight": "auto",
        "locale": "zh-tw", # 設定語系
    }
    state = calendar(events=calendar_events, options=calendar_options, key="roster_cal")

with col2:
    st.subheader("📋 Flight Details")
    
    # 決定要抓哪一班的詳細資料
    final_target = None
    if state.get("eventClick"):
        final_target = state["eventClick"]["event"]["title"].strip()
    elif "selected_f" in st.session_state:
        final_target = st.session_state.selected_f

    if final_target and final_target != "None":
        stay_list = ["150", "151", "130", "131", "731", "732"]
        search_list = [final_target]
        # 如果不是過夜班，自動加一號
        if final_target not in stay_list:
            try: search_list.append(str(int(final_target) + 1))
            except: pass
            
        found = False
        for t in search_list:
            # 精準搜尋：避免 contains 抓到 117 時也抓到 117A 這種
            match = df[df['班號'] == t]
            if not match.empty:
                r = match.iloc[0]
                found = True
                tag_txt = "GO" if (len(search_list)>1 and t==final_target) else ("RTN" if len(search_list)>1 else "STAY")
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h2 style='color:{WARM_PINK}; margin:0;'>CI {t}</h2>
                            <span class="tag-go">{tag_txt}</span>
                        </div>
                        <p style='margin:18px 0 6px 0; font-size:1.4rem; font-weight:700;'>📍 <b>{r['目的地']}</b></p>
                        <p style='font-size:1.1rem; color:#CCC;'>⏰ 報到: <span style='color:{WARM_PINK}; font-weight:800;'>{r.get('報到時間','--:--')}</span></p>
                        <hr style='border-color:#444; margin:15px 0;'>
                        <p style='margin:0; font-size:1.1rem; color:#AAA;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
        if not found: st.warning(f"CSV 裡找不到 {final_target}")
    elif final_target == "None":
        st.info("今天沒有排班喔，好好休息！☕")
    else:
        st.write("✨ 點擊月曆班號，或按大按鈕看今天班表")
