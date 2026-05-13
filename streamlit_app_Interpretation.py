import streamlit as st

# --- 1. 页面配置 ---
st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# --- 2. 配置区域 ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

# --- 3. 构造注入式 HTML/JS ---
# 使用 st.markdown 注入主页面，解决 TypeError 和 麦克风拦截问题
st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
    等待翻译中...
</div>
<button id="vapi-start-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">开始实时翻译</button>
<p id="vapi-status-text" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">连接状态: 正在初始化...</p>

<script type="module">
    import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

    const subtitleBox = document.getElementById('subtitle-box');
    const statusText = document.getElementById('vapi-status-text');
    const startBtn = document.getElementById('vapi-start-btn');

    let vapi = null;
    let ws = null;

    // 1. 初始化 Vapi
    try {{
        vapi = new Vapi("{VAPI_PUBLIC_KEY}");
        statusText.innerText = "✅ 系统就绪";
    }} catch (err) {{
        statusText.innerText = "❌ 引擎初始化失败";
    }}

    // 2. WebSocket 翻译推送逻辑 [cite: 19, 20, 21]
    const connectWS = () => {{
        ws = new WebSocket("{WSS_URL}");
        ws.onopen = () => {{
            statusText.innerText = "✅ 已连接到翻译后端";
            statusText.style.color = "#00cc66";
        }};
        ws.onmessage = (e) => {{
            const data = JSON.parse(e.data);
            if (data.translation) {{
                subtitleBox.innerHTML = `<div style="color:#ffcc00;">${{data.translation}}</div>`;
            }}
        }};
        ws.onclose = () => setTimeout(connectWS, 3000);
    }};
    connectWS();

    // 3. 监听 Vapi 事件 [cite: 22, 23, 24]
    vapi.on('call-start', () => {{
        statusText.innerText = "🎙️ 正在实时翻译...";
        statusText.style.color = "#ffcc00";
        startBtn.innerText = "停止翻译";
        startBtn.style.backgroundColor = "#ff4b4b";
    }});

    vapi.on('call-end', () => {{
        statusText.innerText = "✅ 系统就绪";
        statusText.style.color = "#00cc66";
        startBtn.innerText = "开始实时翻译";
        startBtn.style.backgroundColor = "#00cc66";
    }});

    vapi.on('error', (err) => {{
        console.error('Vapi Error:', err);
        statusText.innerText = "❌ 麦克风调用失败 (请检查域名权限)";
        statusText.style.color = "#ff4b4b";
    }});

    // 4. 按钮控制逻辑 [cite: 25, 26]
    startBtn.onclick = async () => {{
        if (startBtn.innerText === "开始实时翻译") {{
            try {{
                statusText.innerText = "正在请求麦克风...";
                await vapi.start("{VAPI_ASSISTANT_ID}");
            }} catch (e) {{
                console.error("Start failed", e);
            }}
        }} else {{
            vapi.stop();
        }}
    }};
</script>
"""

# --- 4. 关键：绕过 Iframe，直接注入 ---
st.markdown(st_html, unsafe_allow_html=True)