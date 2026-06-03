import os
import urllib.parse

import folium
import requests
import streamlit as st
from streamlit_folium import st_folium


st.set_page_config(page_title="Multi-Engine Map", layout="wide")

# 地图引擎
# 注意：Google Maps 的瓦片地址通常可用于快速预览，但正式生产环境请确认符合 Google Maps Platform 使用条款。
MAP_ENGINES = {
    "OpenStreetMap": "OpenStreetMap",
    "Google Road Map": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    "Google Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    "Google Terrain": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
    "Google Hybrid": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
}

DEFAULT_CITY_SUFFIX = "Calgary, AB, Canada"


def get_google_maps_api_key() -> str | None:
    """
    优先从 Streamlit secrets 读取，其次从环境变量读取。

    Streamlit Cloud / secrets.toml:
        GOOGLE_MAPS_API_KEY = "你的 key"

    本地环境变量:
        Windows PowerShell:
            $env:GOOGLE_MAPS_API_KEY="你的 key"

        macOS/Linux:
            export GOOGLE_MAPS_API_KEY="你的 key"
    """
    try:
        key_from_secrets = st.secrets.get("GOOGLE_MAPS_API_KEY")
        if key_from_secrets:
            return str(key_from_secrets)
    except Exception:
        pass

    return os.getenv("GOOGLE_MAPS_API_KEY")


def build_query(user_input: str, local_search: bool = True) -> str:
    """
    local_search=True:
        如果用户没有输入明显的城市/省/国家信息，则默认补 Calgary, AB, Canada。
        这样搜索中文商户名时，会优先限制在 Calgary 附近。

    local_search=False:
        用户输入什么，就直接交给 Google Maps 搜索。
        适合搜索全球地点，例如 time square / tokyo tower / shibuya crossing。
    """
    clean_input = (user_input or "").strip()

    if not clean_input:
        return DEFAULT_CITY_SUFFIX

    if not local_search:
        return clean_input

    lower_input = clean_input.lower()

    # 如果用户输入里已经有明显地理信息，就不要强行补 Calgary
    location_hints = [
        # Canada / local
        "calgary",
        "alberta",
        " ab",
        "canada",
        " ca",
        "toronto",
        "vancouver",
        "montreal",
        "ottawa",
        "edmonton",
        "winnipeg",
        "halifax",

        # US
        "new york",
        "ny",
        "usa",
        "united states",
        "us",
        "los angeles",
        "san francisco",
        "seattle",
        "chicago",
        "boston",
        "washington",
        "las vegas",

        # common global cities
        "london",
        "paris",
        "tokyo",
        "osaka",
        "kyoto",
        "shibuya",
        "hong kong",
        "singapore",
        "taipei",
        "beijing",
        "shanghai",
        "seoul",
        "sydney",
    ]

    if any(hint in lower_input for hint in location_hints):
        return clean_input

    return f"{clean_input}, {DEFAULT_CITY_SUFFIX}"


def geocode_with_google(query: str, api_key: str, local_search: bool = True) -> dict | None:
    """
    使用 Google Maps Geocoding API 搜索地址/商户。
    返回统一后的 location dict，方便后面 folium 使用。

    重要：
    - 不再使用 components=country:CA，否则会导致 time square 这类美国地址搜不到。
    - local_search=True 时，只用 region=ca 作为轻微偏向，而不是强制限制。
    """
    endpoint = "https://maps.googleapis.com/maps/api/geocode/json"

    params = {
        "address": query,
        "key": api_key,
        "language": "en",
    }

    # 只作为轻微加拿大偏向，不会像 components=country:CA 那样强制限制国家
    if local_search:
        params["region"] = "ca"

    response = requests.get(endpoint, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    status = data.get("status")

    if status == "OK" and data.get("results"):
        result = data["results"][0]
        geometry = result.get("geometry", {})
        lat_lng = geometry.get("location", {})

        formatted_address = result.get("formatted_address", query)
        place_id = result.get("place_id", "")

        google_maps_url = (
            "https://www.google.com/maps/search/?api=1"
            f"&query={urllib.parse.quote_plus(formatted_address)}"
        )

        if place_id:
            google_maps_url += f"&query_place_id={urllib.parse.quote_plus(place_id)}"

        return {
            "address": formatted_address,
            "latitude": lat_lng.get("lat"),
            "longitude": lat_lng.get("lng"),
            "place_id": place_id,
            "google_maps_url": google_maps_url,
            "raw_status": status,
        }

    if status == "ZERO_RESULTS":
        return None

    error_message = data.get("error_message") or status or "Unknown Google Maps API error"
    raise RuntimeError(error_message)


def create_map(location: dict, selected_engine: str) -> folium.Map:
    tiles_value = MAP_ENGINES[selected_engine]

    if selected_engine.startswith("Google"):
        attr = "Google"
    else:
        attr = None

    m = folium.Map(
        location=[location["latitude"], location["longitude"]],
        zoom_start=16,
        tiles=tiles_value,
        attr=attr,
    )

    popup_html = f"""
    <b>{location["address"]}</b><br>
    <a href="{location["google_maps_url"]}" target="_blank">Open in Google Maps</a>
    """

    # 自定义水滴状 marker，不依赖 Leaflet 默认 marker 图片
    pin_html = """
    <div style="
        position: relative;
        width: 34px;
        height: 48px;
    ">
        <div style="
            position: absolute;
        left: 4px;
        top: 0;
        width: 22px;
        height: 34px;
        background: #ff0000;
        border: 3px solid white;
        border-radius: 50% 50% 50% 0;
        transform: rotate(-45deg);
        box-shadow: 0 3px 8px rgba(0,0,0,0.35);
        ">
            <div style="
                width: 10px;
                height: 10px;
                background: white;
                border-radius: 50%;
                margin: 9px;
            "></div>
        </div>
    </div>
    """

    folium.Marker(
        location=[location["latitude"], location["longitude"]],
        popup=folium.Popup(popup_html, max_width=320),
        tooltip=location["address"],
        icon=folium.DivIcon(
            html=pin_html,
            icon_size=(34, 48),
            icon_anchor=(17, 38),
            popup_anchor=(0, -38),
        ),
    ).add_to(m)

    return m


st.title("🗺️ Multi-engine Map Locator - Allison & Bryan")

with st.sidebar:
    st.header("Options")

    selected_engine = st.selectbox(
        "Select Map Engine:",
        list(MAP_ENGINES.keys()),
    )

    user_input = st.text_input(
        "Enter address, business name, landmark, or postal code:",
        value="Landmarks Marketmall",
    )

    local_search = st.checkbox(
        "Prefer Calgary local search",
        value=True,
        help=(
            "勾选后，如果没有输入城市/国家，会默认补 Calgary, AB, Canada。"
            "取消勾选后，可以搜索全球地点，例如 time square。"
        ),
    )

    st.caption("Search engine: Google Maps Geocoding API")

    if local_search:
        st.info("Current mode: Calgary local search")
    else:
        st.info("Current mode: Global search")


api_key = get_google_maps_api_key()

if not api_key:
    st.error(
        "缺少 GOOGLE_MAPS_API_KEY。请先把 Google Maps API key 放到 Streamlit secrets "
        "或系统环境变量 GOOGLE_MAPS_API_KEY 里。"
    )
    st.stop()


query = build_query(user_input, local_search)

st.write(f"**Search query sent to Google Maps:** `{query}`")

try:
    location = geocode_with_google(query, api_key, local_search)

    if (
        location
        and location.get("latitude") is not None
        and location.get("longitude") is not None
    ):
        m = create_map(location, selected_engine)

        st_folium(
            m,
            width="100%",
            height=600,
            key="main_map",
        )

        st.write(f"**当前位置:** {location['address']}")
        st.write(f"**坐标:** {location['latitude']}, {location['longitude']}")
        st.link_button("Open in Google Maps", location["google_maps_url"])

    else:
        st.warning(
            "Google Maps 未找到该位置。可以试试：\n\n"
            "- 如果你在搜 Calgary 本地商户，保持 Calgary local search 勾选。\n"
            "- 如果你在搜全球地点，例如 time square，请取消 Calgary local search。\n"
            "- 或者输入更完整的城市/国家信息，例如 `Times Square, New York`。"
        )

except requests.exceptions.Timeout:
    st.error("Google Maps API 请求超时，请稍后再试。")

except requests.exceptions.HTTPError as e:
    st.error(f"Google Maps API HTTP 错误: {e}")

except Exception as e:
    st.error(f"发生错误: {e}")