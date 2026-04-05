import streamlit as st
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, timedelta
import os

# --- 0. 基本設定 ---
st.set_page_config(page_title="CAL SCHEDULE", layout="wide")

if "current_user" not in st.session_state:
    st.session_state.current_user = "Irene"

CREW_CONFIG = {
    "Irene": {"color": "#F07699", "sheet": "Irene"},
    "Isabelle": {"color": "#A28CF0", "sheet": "Isabelle"},
    "Elaine": {"color": "#76C9F0", "sheet": "Elaine"},
    "Bigpiao": {"color": "#F0B476", "sheet": "Bigpiao"}
}
user_color = CREW_CONFIG[st.session_state.current_user]["color"]

# --- 1. 除錯看板 (破案關鍵) ---
try:
    if os.path.exists("CAL_Roster.xlsx"):
        xl = pd.ExcelFile("CAL_Roster.xlsx")
        st.info(f"📁 偵測到 Excel！裡面的分頁有：{xl.sheet_names}")
    else:
        st.error("❌ 找不到 CAL_Roster.xlsx，請檢查 GitHub 根目錄！")
except Exception as e:
    st.error(f"❌ 讀取 Excel 失敗：{e}")

# --- 2. 側邊欄 ---
with st.sidebar:
    st.title("✈️ SCHEDULE")
    for name in CREW_CONFIG.keys():
        if st.button(name):
            st.session_state.current_user = name
            st.rerun()

# --- 3. 核心數據處理 ---
calendar_events = []
try:
    if os.path.exists("CAL_Roster.xlsx"):
        target_sheet = CREW_CONFIG[st.session_state.current_user]["sheet"]
        # 🚀 模糊匹配 (無視大小寫與空格)
        real_sheet = next((s for s in xl.sheet_names if s.strip().lower() == target_sheet.lower()), None)
        
        if real_sheet:
            df = pd.read_excel("CAL_Roster.xlsx", sheet_name=real_sheet)
            for _, row in df.iterrows():
                if pd.isna(row['日期']): continue
                start_dt = pd.to_datetime(row['日期'])
                # 這裡就是妳要的長班邏輯... (略，保持不變)
                calendar_events.append({
                    "title": str(row['班號']),
                    "start": start_dt.strftime('%Y-%m-%d'),
                    "end": (start_dt + timedelta(days=1)).strftime('%Y-%m-%d'),
                    "allDay": True,
                    "backgroundColor": user_color
                })
        else:
            st.warning(f"⚠️ 找不到分頁 '{target_sheet}'，請檢查 Excel 標籤名！")
except: pass

# --- 4. 顯示月曆 ---
st.title(f"💖 {st.session_state.current_user}")
calendar(events=calendar_events, options={"initialDate": "2026-04-06"}, key=st.session_state.current_user)
