import json
import math
import re
import urllib.parse
import urllib.request
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

# ---- 跟遊戲裡 ORIGIN 完全一樣的座標換算（經緯度 → 公尺） ----
ORIGIN_LAT, ORIGIN_LNG = 25.04163, 121.54367
M_LAT = 110950
M_LNG = 111320 * math.cos(25.04 * math.pi / 180)

# 抓資料的範圍：忠孝復興 ~ 台北101 周邊
SOUTH, WEST, NORTH, EAST = 25.0310, 121.5395, 25.0450, 121.5695

OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]
ROAD_WIDTH = {"trunk": 20, "primary": 18, "secondary": 14, "tertiary": 11,
              "unclassified": 8, "residential": 7, "living_street": 6, "service": 5}


def to_local(lat, lng):
    return round((lng - ORIGIN_LNG) * M_LNG, 1), round(-(lat - ORIGIN_LAT) * M_LAT, 1)


def parse_height(tags):
    h = tags.get("height")
    if h:
        m = re.match(r"[\d.]+", h)
        if m:
            try:
                return round(float(m.group()), 1)
            except ValueError:
                pass
    lv = tags.get("building:levels")
    if lv:
        m = re.match(r"[\d.]+", lv)
        if m:
            try:
                return round(float(m.group()) * 3.3, 1)
            except ValueError:
                pass
    return 0  # 0 = 遊戲自己隨機給高度


@st.cache_data(ttl=7 * 24 * 3600, show_spinner="第一次開啟：正在下載台北東區街道資料（約 10–30 秒）…")
def load_osm():
    bbox = f"{SOUTH},{WEST},{NORTH},{EAST}"
    query = f"""[out:json][timeout:90];
(
  way["building"]({bbox});
  way["highway"~"^(trunk|primary|secondary|tertiary|unclassified|residential|living_street|service)$"]({bbox});
);
out geom;"""
    body = urllib.parse.urlencode({"data": query}).encode()
    raw = None
    for url in OVERPASS_URLS:
        try:
            req = urllib.request.Request(url, data=body, headers={"User-Agent": "bond-race-game/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = json.loads(r.read().decode("utf-8"))
            break
        except Exception:
            continue
    if not raw:
        raise RuntimeError("OpenStreetMap 暫時連不上")   # 不快取失敗結果，下次開啟會再試

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
                    flat = flat[:-2]  # 去掉重複的最後一點
                buildings.append([parse_height(tags), flat])
        elif "highway" in tags and len(flat) >= 4:
            roads.append([ROAD_WIDTH.get(tags["highway"], 7), flat])
    if len(buildings) < 30:
        raise RuntimeError("街道資料太少")
    return {"b": buildings, "r": roads}


html = Path(__file__).parent.joinpath("bond_race_city.html").read_text(encoding="utf-8")
try:
    data = load_osm()
except Exception:
    data = None   # 下載失敗就用遊戲內建街景，照樣能玩
payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/") if data else ""
html = html.replace("__OSM_DATA__", payload)

components.html(html, height=900, scrolling=False)
