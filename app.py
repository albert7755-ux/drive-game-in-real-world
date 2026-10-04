import streamlit as st
import streamlit.components.v1 as components
from pathlib import Path

st.set_page_config(page_title="債券賽車", page_icon="🏎️", layout="wide",
                   initial_sidebar_state="collapsed")

# 把 Streamlit 自己的邊框、padding 拿掉，讓遊戲盡量滿版
st.markdown("""
<style>
  #MainMenu, header, footer {visibility: hidden;}
  .block-container {padding: 0 !important; max-width: 100% !important;}
  iframe {display: block; width: 100vw !important; height: 100vh !important; border: 0;}
</style>
""", unsafe_allow_html=True)

api_key = st.secrets.get("GOOGLE_MAPS_API_KEY", "")
if not api_key:
    st.error("還沒設定金鑰：請到 Streamlit Cloud 的 Settings → Secrets 加上 GOOGLE_MAPS_API_KEY")
    st.stop()

html = Path(__file__).parent.joinpath("bond_race_google3d.html").read_text(encoding="utf-8")
html = html.replace("請把你的金鑰貼在這裡", api_key)

components.html(html, height=900, scrolling=False)
