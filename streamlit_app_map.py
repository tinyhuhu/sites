import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.geocoders import ArcGIS

st.set_page_config(page_title="Multi-Engine Map", layout="wide")

# 1. 定义地图引擎字典
# 注意：Google Maps 的瓦片地址通常是公开的，但请遵循其使用条款
MAP_ENGINES = {
    "OpenStreetMap": "OpenStreetMap",
    "Google Road Map": "https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
    "Google Satellite": "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    "Google Terrain": "https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}",
    "Google Hybrid": "https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}",
}

st.title("🗺️ Multi-engine Map Locator")

# 2. 侧边栏配置
with st.sidebar:
    st.header("Options")
    # 下拉框选择引擎
    selected_engine = st.selectbox("Select Map Engine:", list(MAP_ENGINES.keys()))
    
    # 搜索框
    user_input = st.text_input("Enter address or postal-code:", value="Landmarks Marketmall")
    
    #st.info("提示：Google 引擎使用的是其公共瓦片服务，无需 API Key 即可快速预览。")

# 3. 逻辑处理
geolocator = ArcGIS()
query = f"{user_input}, Calgary, AB, Canada" if "Calgary" not in user_input else user_input

try:
    location = geolocator.geocode(query, timeout=10)
    
    if location:
        # 获取选中的引擎配置
        tiles_value = MAP_ENGINES[selected_engine]
        
        # 4. 创建地图
        # 如果是 Google 引擎，需要额外设置 attr 参数
        attr = "Google" if "Google" in selected_engine else None
        
        m = folium.Map(
            location=[location.latitude, location.longitude],
            zoom_start=15,
            tiles=tiles_value,
            attr=attr
        )
        
        folium.Marker(
            [location.latitude, location.longitude],
            popup=location.address
        ).add_to(m)

        # 展示地图
        st_folium(m, width="100%", height=600, key=f"map_{selected_engine}_{location.latitude}")
        
        st.write(f"**当前位置:** {location.address}")
    else:
        st.warning("未找到该位置。")

except Exception as e:
    st.error(f"发生错误: {e}")
