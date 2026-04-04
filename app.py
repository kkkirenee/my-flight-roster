import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime

# --- 1. 頁面與風格設定 ---
st.set_page_config(page_title="CAL Calendar", page_icon="📅", layout="wide")

HOT_PINK = "#FF2E63"
BG_BLACK = "#0E0E0E"

st.markdown(f"""
    <style>
    .stApp {{ background-color: {BG_BLACK}; color: white; }}
    #MainMenu, footer, header {{ visibility: hidden; }}
    .report-card {{
        background: #1A1A1A; border-radius: 15px; padding: 20px;
        border: 1px solid {HOT_PINK}; box-shadow: 0 0 15px rgba(255,46,99,0.2);
        margin-bottom: 12px;
    }}
    .tag {{
        background: {HOT_PINK}; color: white; padding: 2px 8px;
        border-radius: 4px; font-size: 0.75rem; font-weight: 800;
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
for date, flight in ROSTER.items():
    calendar_events.append({
        "title": flight, "start": date, "end": date,
        "backgroundColor": HOT_PINK, "borderColor": HOT_PINK
    })

# --- 3. 讀取 CSV ---
try:
    df = pd.read_csv('my_flights.csv', encoding='utf-8-sig')
    df.columns = df.columns.str.strip()
    df['班號'] = df['班號'].astype(str)
except:
    st.error("找不到 my_flights.csv")
    st.stop()

# --- 4. 顯示介面 ---
st.title("💖 FLIGHT CALENDAR")

col1, col2 = st.columns([2.5, 1])

with col1:
    calendar_options = {
        "headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"},
        "initialView": "dayGridMonth",
        "contentHeight": "auto",
        "eventDisplay": "block",
    }
    custom_css = ".fc-event-title { font-size: 1.3em !important; font-weight: 800 !important; padding: 5px !important; text-align: center !important; }"
    state = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css, key="roster_cal")

with col2:
    st.subheader("📋 Flight Details")
    
    if state.get("eventClick"):
        f_no = state["eventClick"]["event"]["title"].strip()
        
        # --- 核心邏輯修正：改用「排除法」 ---
        # 只要不是這些班號，我們就預設它是當天來回，自動抓下一號
        stay_and_rtn_flights = ["150", "151", "130", "131", "731", "732"] 
        search_list = [f_no]
        
        # 只有當點選的班號「不在」上面的清單中，才自動搜尋下一號
        if f_no not in stay_and_rtn_flights:
            try:
                next_no = str(int(f_no) + 1)
                search_list.append(next_no)
            except:
                pass
            
        found_any = False
        for target in search_list:
            # 在 CSV 中尋找包含該數字的列
            match = df[df['班號'].str.contains(target)]
            if not match.empty:
                r = match.iloc[0]
                found_any = True
                tag_label = "GO" if (len(search_list) > 1 and target == f_no) else ("RTN" if (len(search_list) > 1) else "STAY")
                
                st.markdown(f"""
                    <div class="report-card">
                        <div style='display:flex; justify-content:space-between;'>
                            <h2 style='color:{HOT_PINK}; margin:0;'>CI {target}</h2>
                            <span class="tag">{tag_label}</span>
                        </div>
                        <p style='margin:10px 0 5px 0;'>📍 <b>目的地:</b> {r['目的地']}</p>
                        <p>⏰ <b>報到:</b> <span style='color:{HOT_PINK}'>{r.get('報到時間', '--:--')}</span></p>
                        <hr style='border-color:#333; margin:10px 0;'>
                        <p style='margin:0; font-size:0.9rem; opacity:0.8;'>🛫 {r['起飛時間']} | 🛬 {r['落地時間']}</p>
                    </div>
                """, unsafe_allow_html=True)
        
        if not found_any:
            st.warning(f"CSV 裡找不到班號 {f_no} 的資料")
    else:
        st.write("點擊月曆查看詳情")
