import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# 1. 配置区域
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

# 2. 嵌入 JavaScript 逻辑
st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
    等待翻译中...
</div>
<button id="start-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">开始实时翻译</button>
<p id="status-text" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">连接状态: 正在初始化...</p>

<script type="module">
    // 使用 esm.sh 引入 Vapi，这是目前最稳定且支持直接在浏览器 import 的方式
    import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

    const subtitleBox = document.getElementById('subtitle-box');
    const statusText = document.getElementById('status-text');
    const startBtn = document.getElementById('start-btn');

    let ws;
    let vapi;

    try {{
        vapi = new Vapi("{VAPI_PUBLIC_KEY}");
        console.log("Vapi initialized successfully");
    }} catch (e) {{
        console.error("Vapi init error:", e);
        statusText.innerText = "❌ Vapi 初始化失败";
    }}

    // --- WebSocket 逻辑 ---
    function connectWebSocket() {{
        ws = new WebSocket("{WSS_URL}");

        ws.onopen = () => {{
            statusText.innerText = "✅ 已通过 API Gateway 连接";
            statusText.style.color = "#00cc66";
        }};

        ws.onmessage = (event) => {{
            try {{
                const data = JSON.parse(event.data);
                if (data.translation) {{
                    subtitleBox.innerHTML = `<div style="color:#ffcc00;">${{data.translation}}</div>`;
                }}
            }} catch (e) {{
                console.error("Parse error:", e);
            }}
        }};

        ws.onclose = () => {{
            statusText.innerText = "❌ 连接已断开，正在尝试重连...";
            statusText.style.color = "#ff4b4b";
            setTimeout(connectWebSocket, 3000);
        }};
    }}

    connectWebSocket();

    // --- Vapi 事件 ---
    vapi.on('call-start', () => {{
        statusText.innerText = "🎙️ 正在监听并实时翻译...";
        statusText.style.color = "#ffcc00";
    }});

    vapi.on('call-end', () => {{
        statusText.innerText = "✅ 已通过 API Gateway 连接";
        statusText.style.color = "#00cc66";
    }});

    vapi.on('error', (error) => {{
        console.error('Vapi Error:', error);
        statusText.innerText = "❌ Vapi 呼叫错误";
    }});

    // --- 按钮逻辑 ---
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