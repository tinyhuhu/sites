import os
import urllib.parse

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(page_title="Multi-Engine Map", layout="wide")

# 1. 定义地图引擎字典
# 注意：Google Maps 的瓦片地址通常可用于快速预览，但正式生产环境请确认符合 Google Maps Platform 使用条款。
MAP_ENGINES = {
    "OpenStreetMap": "OpenStreetMap",
    "Google Road Map": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    "Google Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    "Google Terrain": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
    "Google Hybrid": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
}

#DEFAULT_CITY_SUFFIX = "Calgary, AB, Canada"


def get_google_maps_api_key() -> str | None:
    """
    优先从 Streamlit secrets 读取，其次从环境变量读取。

    Streamlit Cloud / secrets.toml:
        GOOGLE_MAPS_API_KEY = "你的 key"

    本地环境变量:
        set GOOGLE_MAPS_API_KEY=你的 key      # Windows PowerShell/CMD 视情况调整
        export GOOGLE_MAPS_API_KEY=你的 key   # macOS/Linux
    """
    try:
        key_from_secrets = st.secrets.get("GOOGLE_MAPS_API_KEY")
        if key_from_secrets:
            return str(key_from_secrets)
    except Exception:
        pass

    return os.getenv("GOOGLE_MAPS_API_KEY")


def build_query(user_input: str) -> str:
    """
    默认不再强制补 Calgary。
    用户输入什么，就直接交给 Google Maps 搜索。
    如果用户想搜 Calgary 本地，可以自己输入 Calgary，或者后面再加一个 checkbox 控制。
    """
    clean_input = (user_input or "").strip()
    if not clean_input:
        return DEFAULT_CITY_SUFFIX

    return clean_input


def geocode_with_google(query: str, api_key: str) -> dict | None:
    """
    使用 Google Maps Geocoding API 搜索地址/商户。
    返回统一后的 location dict，方便后面 folium 使用。
    """
    endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": query,
        "key": api_key,
        "language": "en",
    }

    response = requests.get(endpoint, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    status = data.get("status")

    if status == "OK" and data.get("results"):
        result = data["results"][0]
        geometry = result.get("geometry", {})
        lat_lng = geometry.get("location", {})

        return {
            "address": result.get("formatted_address", query),
            "latitude": lat_lng.get("lat"),
            "longitude": lat_lng.get("lng"),
            "place_id": result.get("place_id", ""),
            "google_maps_url": (
                "https://www.google.com/maps/search/?api=1"
                f"&query={urllib.parse.quote_plus(result.get('formatted_address', query))}"
                f"&query_place_id={urllib.parse.quote_plus(result.get('place_id', ''))}"
            ),
        }

    if status == "ZERO_RESULTS":
        return None

    error_message = data.get("error_message") or status or "Unknown Google Maps API error"
    raise RuntimeError(error_message)


st.title("🗺️ Multi-engine Map Locator - Allison & Bryan")

# 2. 侧边栏配置
with st.sidebar:
    st.header("Options")

    selected_engine = st.selectbox("Select Map Engine:", list(MAP_ENGINES.keys()))

    user_input = st.text_input(
        "Enter address, business name, or postal code:",
        value="Landmarks Marketmall",
    )

    st.caption("Search engine: Google Maps Geocoding API")

# 3. 逻辑处理
api_key = get_google_maps_api_key()
query = build_query(user_input)

if not api_key:
    st.error(
        "缺少 GOOGLE_MAPS_API_KEY。请先把 Google Maps API key 放到 Streamlit secrets "
        "或系统环境变量 GOOGLE_MAPS_API_KEY 里。"
    )
    st.stop()

try:
    location = geocode_with_google(query, api_key)

    if location and location.get("latitude") is not None and location.get("longitude") is not None:
        tiles_value = MAP_ENGINES[selected_engine]
        attr = "Google" if "Google" in selected_engine else None

        m = folium.Map(
            location=[location["latitude"], location["longitude"]],
            zoom_start=15,
            tiles=tiles_value,
            attr=attr,
        )

        popup_html = f"""
        <b>{location["address"]}</b><br>
        <a href="{location["google_maps_url"]}" target="_blank">Open in Google Maps</a>
        """

        folium.Marker(
            [location["latitude"], location["longitude"]],
            popup=folium.Popup(popup_html, max_width=320),
            tooltip=location["address"],
        ).add_to(m)

        st_folium(m, width="100%", height=600, key="main_map")

        st.write(f"**当前位置:** {location['address']}")
        st.write(f"**坐标:** {location['latitude']}, {location['longitude']}")
        st.link_button("Open in Google Maps", location["google_maps_url"])
    else:
        st.warning("Google Maps 未找到该位置。可以试试加上城市、省份，或换一个更完整的商户/地址名称。")

except requests.exceptions.Timeout:
    st.error("Google Maps API 请求超时，请稍后再试。")
except requests.exceptions.HTTPError as e:
    st.error(f"Google Maps API HTTP 错误: {e}")
except Exception as e:
    st.error(f"发生错误: {e}")
