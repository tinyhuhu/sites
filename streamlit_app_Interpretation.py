import streamlit as st
import streamlit.components.v1 as components

# --- 1. 页面配置 ---
st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# --- 2. 配置参数 [cite: 31] ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

# --- 3. HTML 与 JavaScript 逻辑 ---
st_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        #subtitle-box {{
            background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px;
            min-height: 120px; font-size: 24px; font-weight: bold; text-align: center;
            margin-bottom: 20px; border: 2px solid #333; display: flex; align-items: center; justify-content: center;
        }}
        #start-btn {{
            width: 100%; height: 60px; background-color: #00cc66; color: white; border: none;
            border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;
        }}
        #status-text {{ color: #888; font-size: 14px; text-align: center; margin-top: 10px; }}
    </style>
</head>
<body>
    <div id="subtitle-box">等待翻译中...</div>
    <button id="start-btn">开始实时翻译</button>
    <p id="status-text">连接状态: 正在初始化设备...</p>

    <script type="module">
        import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

        const subtitleBox = document.getElementById('subtitle-box');
        const statusText = document.getElementById('status-text');
        const startBtn = document.getElementById('start-btn');
        const vapi = new Vapi("{VAPI_PUBLIC_KEY}");
        let ws;

        // WebSocket 连接逻辑 [cite: 35, 36, 37]
        function connectWebSocket() {{
            ws = new WebSocket("{WSS_URL}");
            ws.onopen = () => {{
                statusText.innerText = "✅ 已通过 API Gateway 连接";
                statusText.style.color = "#00cc66";
            }};
            ws.onmessage = (event) => {{
                const data = JSON.parse(event.data);
                if (data.translation) {{
                    subtitleBox.innerHTML = `<div style="color:#ffcc00;">${{data.translation}}</div>`;
                }}
            }};
            ws.onclose = () => {{ setTimeout(connectWebSocket, 3000); }};
        }}
        connectWebSocket();

        // 绑定 Vapi 事件 [cite: 38, 39, 40]
        vapi.on('call-start', () => {{
            statusText.innerText = "🎙️ 正在监听并实时翻译...";
            statusText.style.color = "#ffcc00";
            startBtn.innerText = "停止翻译";
            startBtn.style.backgroundColor = "#ff4b4b";
        }});

        vapi.on('call-end', () => {{
            statusText.innerText = "✅ 已就绪";
            statusText.style.color = "#00cc66";
            startBtn.innerText = "开始实时翻译";
            startBtn.style.backgroundColor = "#00cc66";
        }});

        vapi.on('error', (err) => {{
            console.error('Vapi Error:', err);
            statusText.innerText = "❌ 麦克风开启失败 (请检查权限)";
            statusText.style.color = "#ff4b4b";
        }});

        // 按钮点击逻辑 [cite: 41, 42]
        startBtn.onclick = async () => {{
            if (startBtn.innerText === "开始实时翻译") {{
                try {{
                    statusText.innerText = "正在请求麦克风并呼叫...";
                    await vapi.start("{VAPI_ASSISTANT_ID}");
                }} catch (e) {{
                    console.error("Start failed", e);
                }}
            }} else {{
                vapi.stop();
            }}
        }};
    </script>
</body>
</html>
"""

# --- 4. 关键修复：添加 allow="microphone" ---
# Streamlit 1.25.0+ 支持在 components.html 中传递 allow 参数
try:
    components.html(
        st_html, 
        height=600, 
        scrolling=False,
        allow="microphone" # 核心修复：显式允许麦克风权限
    )
except TypeError:
    # 兼容非常旧的 Streamlit 版本，如果不支持 allow 参数
    components.html(
        st_html, 
        height=600, 
        scrolling=False
    )