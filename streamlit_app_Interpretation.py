import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# 1. 配置区域
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

# 2. 嵌入修复后的 JavaScript 逻辑
st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
    等待翻译中...
</div>
<button id="start-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">开始实时翻译</button>
<p id="status-text" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">连接状态: 正在初始化...</p>

<script type="module">
    import Vapi from 'https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/+esm';

    const subtitleBox = document.getElementById('subtitle-box');
    const statusText = document.getElementById('status-text');
    const startBtn = document.getElementById('start-btn');

    let ws;
    const vapi = new Vapi("{VAPI_PUBLIC_KEY}");

    // --- 核心修改：断线重连逻辑 ---
    function connectWebSocket() {{
        ws = new WebSocket("{WSS_URL}");

        ws.onopen = () => {{
            statusText.innerText = "✅ 已通过 API Gateway 连接";
            statusText.style.color = "#00cc66";
            console.log("WebSocket Connected");
        }};

        ws.onmessage = (event) => {{
            try {{
                const data = JSON.parse(event.data);
                if (data.translation) {{
                    subtitleBox.innerHTML = `<div style="color:#ffcc00;">${{data.translation}}</div>`;
                }}
            }} catch (e) {{
                console.error("解析消息失败", e);
            }}
        }};

        ws.onclose = () => {{
            statusText.innerText = "❌ 连接已断开，正在尝试重连...";
            statusText.style.color = "#ff4b4b";
            // 3秒后尝试重新建立连接
            setTimeout(connectWebSocket, 3000);
        }};

        ws.onerror = (err) => {{
            console.error("WebSocket 错误:", err);
            ws.close();
        }};
    }}

    // 初始化连接
    connectWebSocket();

    // --- Vapi 事件处理 ---
    vapi.on('call-start', () => {{
        statusText.innerText = "🎙️ 正在监听并实时翻译...";
        statusText.style.color = "#ffcc00";
    }});

    vapi.on('call-end', () => {{
        statusText.innerText = "✅ 已通过 API Gateway 连接";
        statusText.style.color = "#00cc66";
    }});

    // --- 按钮控制 ---
    startBtn.addEventListener('click', () => {{
        if (startBtn.innerText === "开始实时翻译") {{
            vapi.start("{VAPI_ASSISTANT_ID}");
            startBtn.innerText = "停止翻译";
            startBtn.style.backgroundColor = "#ff4b4b";
        }} else {{
            vapi.stop();
            startBtn.innerText = "开始实时翻译";
            startBtn.style.backgroundColor = "#00cc66";
        }}
    }});
</script>
"""

components.html(st_html, height=600)