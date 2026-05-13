import streamlit as st
import streamlit.components.v1 as components

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# --- 2. 配置参数 ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
# 确保此 URL 与您在 AWS Lambda (Lambda_Interpretation.txt) 中配置的端点一致 [cite: 1]
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

# --- 3. 构造嵌入的 HTML/JS 内容 ---
st_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: sans-serif; background-color: transparent; margin: 0; padding: 0; }}
        #subtitle-box {{
            background-color: #1a1a1a;
            color: #ffcc00;
            padding: 20px;
            border-radius: 10px;
            min-height: 120px;
            font-size: 24px;
            font-weight: bold;
            text-align: center;
            margin-bottom: 20px;
            border: 2px solid #333;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow-wrap: break-word;
        }}
        #start-btn {{
            width: 100%;
            height: 60px;
            background-color: #666; /* 初始禁用色 */
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 20px;
            cursor: not-allowed;
            font-weight: bold;
            transition: background-color 0.3s;
        }}
        #status-text {{
            color: #888;
            font-size: 14px;
            text-align: center;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div id="subtitle-box">等待翻译中...</div>
    <button id="start-btn" disabled>正在载入 SDK...</button>
    <p id="status-text">连接状态: 正在初始化...</p>

    <script src="https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/dist/vapi.browser.js"></script>

    <script>
    (function() {{
        const subtitleBox = document.getElementById('subtitle-box');
        const statusText = document.getElementById('status-text');
        const startBtn = document.getElementById('start-btn');
        let vapiInstance = null;
        let ws = null;

        // 1. 严格检查 Vapi SDK 是否载入成功
        const checkSdk = setInterval(() => {{
            if (window.Vapi) {{
                clearInterval(checkSdk);
                initApp();
            }}
        }}, 200);

        function initApp() {{
            try {{
                vapiInstance = new window.Vapi("{VAPI_PUBLIC_KEY}");
                startBtn.disabled = false;
                startBtn.style.backgroundColor = "#00cc66";
                startBtn.style.cursor = "pointer";
                startBtn.innerText = "开始实时翻译";
                statusText.innerText = "✅ 设备已就绪";
                console.log("Vapi Initialized");
            }} catch (e) {{
                statusText.innerText = "❌ SDK 初始化失败";
                console.error(e);
            }}

            // 2. 建立 WebSocket 连接逻辑
            function connectWebSocket() {{
                ws = new WebSocket("{WSS_URL}");
                ws.onopen = () => {{
                    console.log("WebSocket Connected");
                    statusText.innerText = "✅ 已连接到翻译后端";
                }};
                ws.onmessage = (e) => {{
                    try {{
                        const data = JSON.parse(e.data);
                        // 处理来自 Lambda 的翻译数据 [cite: 3, 4]
                        if (data.translation) {{
                            subtitleBox.innerHTML = "<div>" + data.translation + "</div>";
                        }}
                    }} catch (err) {{ console.error("WS Parse Error", err); }}
                }};
                ws.onclose = () => setTimeout(connectWebSocket, 3000);
            }}
            connectWebSocket();

            // 3. Vapi 事件监听
            vapiInstance.on('call-start', () => {{
                statusText.innerText = "🎙️ 正在监听电影中...";
                startBtn.innerText = "停止翻译";
                startBtn.style.backgroundColor = "#ff4b4b";
            }});

            vapiInstance.on('call-end', () => {{
                statusText.innerText = "✅ 已停止";
                startBtn.innerText = "开始实时翻译";
                startBtn.style.backgroundColor = "#00cc66";
            }});

            vapiInstance.on('error', (err) => {{
                console.error("Vapi Error:", err);
                statusText.innerText = "❌ 呼叫错误，请检查麦克风";
            }});

            // 4. 按钮控制
            startBtn.onclick = async () => {{
                if (vapiInstance.isCallActive()) {{
                    vapiInstance.stop();
                }} else {{
                    try {{
                        statusText.innerText = "正在开启麦克风...";
                        await vapiInstance.start("{VAPI_ASSISTANT_ID}");
                    }} catch (err) {{
                        console.error("Start Error:", err);
                        alert("麦克风启动失败，请确保授予权限且处于 HTTPS 环境。");
                    }}
                }}
            }};
        }}
    }})();
    </script>
</body>
</html>
"""

# --- 4. 渲染组件 ---
# 这里是关键：显式设置 allow 属性，确保 iframe 拥有麦克风权限
components.html(st_html, height=450, scrolling=False)