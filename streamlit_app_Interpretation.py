import streamlit as st
import json

# --- 1. 页面配置 ---
st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# --- 2. 配置区域 ---
# 请确保这些 ID 与您的 Vapi 控制台和 AWS 环境一致
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

# --- 3. 定义注入的 HTML/JS ---
# 使用 f""" 方便注入 Python 变量，注意 JS 的大括号需要双写 {{ }} 进行转义
st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
    等待翻译中...
</div>

<button id="start-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold; transition: 0.3s;">
    开始实时翻译
</button>

<p id="status-text" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">
    连接状态: 正在初始化设备...
</p>

<script src="https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/dist/vapi.browser.js"></script>

<script>
(function() {{
    let vapiInstance = null;
    let ws = null;

    // 轮询确保 Vapi SDK 加载完成
    const checkSdk = setInterval(() => {{
        if (window.Vapi) {{
            clearInterval(checkSdk);
            initApplication();
        }}
    }}, 100);

    function initApplication() {{
        const subtitleBox = document.getElementById('subtitle-box');
        const statusText = document.getElementById('status-text');
        const startBtn = document.getElementById('start-btn');

        // 初始化 Vapi
        vapiInstance = new window.Vapi("{VAPI_PUBLIC_KEY}");

        // --- WebSocket 通信逻辑 ---
        function connectWebSocket() {{
            ws = new WebSocket("{WSS_URL}");

            ws.onopen = () => {{
                statusText.innerText = "✅ 已连接到翻译服务器";
                statusText.style.color = "#00cc66";
            }};

            ws.onmessage = (event) => {{
                try {{
                    const data = JSON.parse(event.data);
                    if (data.translation) {{
                        subtitleBox.innerHTML = `<div style="color:#ffcc00; animation: fadeIn 0.5s;">${{data.translation}}</div>`;
                    }}
                }} catch (e) {{ console.error("WS Data Error", e); }}
            }};

            ws.onclose = () => {{
                statusText.innerText = "❌ 连接断开，尝试重连...";
                statusText.style.color = "#ff4b4b";
                setTimeout(connectWebSocket, 3000);
            }};
        }}

        connectWebSocket();

        // --- Vapi 事件监听 ---
        vapiInstance.on('call-start', () => {{
            statusText.innerText = "🎙️ 正在实时监听电影对白...";
            statusText.style.color = "#ffcc00";
            startBtn.innerText = "停止翻译";
            startBtn.style.backgroundColor = "#ff4b4b";
        }});

        vapiInstance.on('call-end', () => {{
            statusText.innerText = "✅ 设备已就绪";
            statusText.style.color = "#00cc66";
            startBtn.innerText = "开始实时翻译";
            startBtn.style.backgroundColor = "#00cc66";
        }});

        vapiInstance.on('error', (err) => {{
            console.error('Vapi Error:', err);
            statusText.innerText = "❌ 呼叫错误 (请检查麦克风权限)";
            statusText.style.color = "#ff4b4b";
            startBtn.innerText = "开始实时翻译";
            startBtn.style.backgroundColor = "#00cc66";
        }});

        // --- 按钮点击逻辑 ---
        startBtn.onclick = async () => {{
            if (startBtn.innerText === "开始实时翻译") {{
                try {{
                    statusText.innerText = "正在请求麦克风并呼叫...";
                    // 开启 Vapi 通话
                    await vapiInstance.start("{VAPI_ASSISTANT_ID}");
                }} catch (e) {{
                    console.error("Vapi Start Error", e);
                    alert("无法启动语音监听，请确保浏览器允许麦克风权限。");
                }}
            }} else {{
                vapiInstance.stop();
            }}
        }};
    }}
}})();
</script>

<style>
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}
</style>
"""

# --- 4. 关键注入步骤 ---
# 使用 unsafe_allow_html=True 直接在当前页面域名下运行脚本
# 这样可以绕过 iframe 的 Origin: null 限制，直接继承主页面的权限
st.markdown(st_html, unsafe_allow_html=True)