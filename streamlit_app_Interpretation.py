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


# 注意：在 f"""...""" 中，所有的 JS 大括号必须写成 {{ }}
st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
    等待翻译中...
</div>
<button id="start-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">开始实时翻译</button>
<p id="status-text" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">连接状态: 准备中...</p>

<script src="https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/dist/vapi.browser.js"></script>

<script>
    // --- 配置 ---
    const WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/"; 
    const VAPI_PUBLIC_KEY = "{VAPI_PUBLIC_KEY}";
    const VAPI_ASSISTANT_ID = "{VAPI_ASSISTANT_ID}";

    const subtitleBox = document.getElementById('subtitle-box');
    const statusText = document.getElementById('status-text');
    const startBtn = document.getElementById('start-btn');

    // 2. WebSocket 连接逻辑
    const ws = new WebSocket(WSS_URL);

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

    // 3. Vapi 初始化 (使用浏览器全局对象)
    let vapi = null;
    
    // 确保 Vapi 加载完成后再初始化
    window.onload = () => {{
        vapi = new Vapi(VAPI_PUBLIC_KEY);
        
        vapi.on('call-start', () => {{ 
            statusText.innerText = "🎙️ 正在监听电影对白..."; 
            statusText.style.color = "#ffcc00";
        }});
        
        vapi.on('call-end', () => {{ 
            statusText.innerText = "✅ 已通过 API Gateway 连接";
            statusText.style.color = "#00cc66";
        }});
    }};

    startBtn.addEventListener('click', () => {{
        if (!vapi) return;
        
        if (startBtn.innerText === "开始实时翻译") {{
            vapi.start(VAPI_ASSISTANT_ID);
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