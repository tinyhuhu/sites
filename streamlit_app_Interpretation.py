import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# 1. 配置区域
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
IOT_ENDPOINT = "a3pqsh1g7enzj8-ats.iot.us-east-2.amazonaws.com" 

# 2. 嵌入修复后的 JavaScript 逻辑
# 注意：这里使用了 f"""..."""，因此代码内部所有的 JS 大括号都已转义为 {{ }}
# 1. 配置区域
# 请确保使用 image_55087e.png 中显示的 WebSocket URL
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
    等待翻译中...
</div>
<button id="start-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">开始实时翻译</button>
<p id="status-text" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">连接状态: 准备中...</p>

<script type="module">
    // --- 核心配置 ---
    const WSS_URL = "{WSS_URL}"; 
    const subtitleBox = document.getElementById('subtitle-box');
    const statusText = document.getElementById('status-text');
    let socket;

    function connectWebSocket() {{
        statusText.innerText = "正在建立 WebSocket 连接...";
        
        // 使用原生浏览器 WebSocket，无需签名和额外库
        socket = new WebSocket(WSS_URL);

        socket.onopen = () => {{
            statusText.innerText = "✅ 已通过 API Gateway 连接";
            statusText.style.color = "#00cc66";
            console.log("WebSocket Connected");
        }};

        socket.onmessage = (event) => {{
            try {{
                const data = JSON.parse(event.data);
                if (data.translation) {{
                    subtitleBox.innerHTML = `<div style="color:#ffcc00;">${{data.translation}}</div>`;
                }}
            }} catch (err) {{
                console.error("解析消息失败:", err);
            }}
        }};

        socket.onclose = () => {{
            statusText.innerText = "❌ 连接已断开，正在尝试重连...";
            statusText.style.color = "#ff4444";
            setTimeout(connectWebSocket, 3000); // 3秒后自动重连
        }};

        socket.onerror = (error) => {{
            statusText.innerText = "❌ WebSocket 错误";
            console.error("WebSocket Error:", error);
        }};
    }}

    // 页面加载完成后立即连接
    connectWebSocket();
    
    // ... 这里保留你原有的 Vapi 逻辑 ...
</script>
"""

components.html(st_html, height=600)