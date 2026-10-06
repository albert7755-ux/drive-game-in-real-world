import csv
import io
import json
import math
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

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

here = Path(__file__).parent

# ---- 跟遊戲裡 ORIGIN 完全一樣的座標換算（經緯度 → 公尺） ----
ORIGIN_LAT, ORIGIN_LNG = 25.04163, 121.54367
M_LAT = 110950
M_LNG = 111320 * math.cos(25.04 * math.pi / 180)
ROAD_WIDTH = {"trunk": 20, "primary": 18, "secondary": 14, "tertiary": 11,
              "unclassified": 8, "residential": 7, "living_street": 6, "service": 5}


def to_local(lat, lng):
    return round((lng - ORIGIN_LNG) * M_LNG, 1), round(-(lat - ORIGIN_LAT) * M_LAT, 1)


def parse_height(tags):
    for key, mult in (("height", 1.0), ("building:levels", 3.3)):
        m = re.match(r"[\d.]+", tags.get(key, "") or "")
        if m:
            try:
                return round(float(m.group()) * mult, 1)
            except ValueError:
                pass
    return 0  # 0 = 遊戲自己隨機給高度


# ---- 真實街道：讀 repo 裡的 taipei_streets.json（不再上網下載，開啟不用等）----
@st.cache_data(show_spinner=False)
def load_streets(path_str, mtime):
    raw = json.loads(Path(path_str).read_text(encoding="utf-8"))
    buildings, roads = [], []
    for el in raw.get("elements", []):
        geom = el.get("geometry")
        if el.get("type") != "way" or not geom:
            continue
        tags = el.get("tags", {})
        flat = []
        for g in geom:
            x, z = to_local(g["lat"], g["lon"])
            flat += [x, z]
        if "building" in tags:
            if len(flat) >= 8:
                if flat[:2] == flat[-2:]:
                    flat = flat[:-2]
                buildings.append([parse_height(tags), flat])
        elif "highway" in tags and len(flat) >= 4:
            roads.append([ROAD_WIDTH.get(tags["highway"], 7), flat])
    return {"b": buildings, "r": roads} if len(buildings) >= 30 else None


def get_streets():
    files = sorted(here.rglob("*taipei_streets*.json"))
    if not files:
        return None
    try:
        return load_streets(str(files[0]), files[0].stat().st_mtime)
    except Exception:
        return None   # 檔案有問題就用內建街景


# ---- 債券條件：讀 bond_settings.csv（可以用 Excel 編輯）----
def load_bond_settings():
    found = sorted(here.rglob("*bond_settings*.csv"))
    if not found:
        return None
    raw = found[0].read_bytes()
    text = None
    for enc in ("utf-8-sig", "cp950", "big5"):   # Excel 存的 CSV 可能是 UTF-8 或 Big5
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        return None
    facts = []
    for row in csv.reader(io.StringIO(text)):
        cells = [c.strip() for c in row]
        if len(cells) < 2 or not cells[0] or not cells[1]:
            continue
        if cells[0] in ("條件", "key", "KEY"):          # 跳過標題列
            continue
        options = [c for c in cells[2:] if c and c != cells[1]][:3]
        facts.append({"key": cells[0], "value": cells[1], "options": options})
    return facts if len(facts) >= 2 else None


# ---- 組合遊戲頁面 ----
found = sorted(here.rglob("*bond_race_city*.html"))
if not found:
    st.error("找不到遊戲檔 bond_race_city.html，請確認它已上傳到這個 GitHub repo。")
    st.write("目前 repo 裡的檔案：", [str(p.relative_to(here)) for p in here.rglob("*") if p.is_file() and ".git" not in p.parts])
    st.stop()
html = found[0].read_text(encoding="utf-8")

streets = get_streets()
html = html.replace("__OSM_DATA__", json.dumps(streets, separators=(",", ":")).replace("</", "<\\/") if streets else "")

try:
    bond = load_bond_settings()
except Exception:
    bond = None   # 設定檔有問題就用遊戲內建的預設值
html = html.replace("__BOND_DATA__", json.dumps(bond, ensure_ascii=False).replace("</", "<\\/") if bond else "")

components.html(html, height=900, scrolling=False)
