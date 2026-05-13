import streamlit as st
import streamlit.components.v1 as components

# --- 1. 页面配置 ---
st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# --- 2. 配置区域 ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85" [cite: 9]
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6" [cite: 9]
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" [cite: 9]

# --- 3. 构造 HTML ---
st_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: sans-serif; background-color: transparent; margin: 0; padding: 0; }}
        #subtitle-box {{
            background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px;
            min-height: 120px; font-size: 24px; font-weight: bold; text-align: center;
            margin-bottom: 20px; border: 2px solid #333; display: flex; align-items: center; justify-content: center;
        }}
        #start-btn {{
            width: 100%; height: 60px; background-color: #666; color: white;
            border: none; border-radius: 8px; font-size: 20px; cursor: not-allowed;
            font-weight: bold; transition: 0.3s;
        }}
        #status-text {{ color: #888; font-size: 14px; text-align: center; margin-top: 10px; }}
    </style>
</head>
<body>
    <div id="subtitle-box">等待翻译中...</div>
    <button id="start-btn" disabled>正在初始化 AI 引擎...</button>
    <p id="status-text">状态: 正在加载依赖...</p>

    <script type="module">
        // 使用 esm.sh 替代 jsdelivr，这在 Streamlit 环境中通常更稳定
        import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2'; 

        const subtitleBox = document.getElementById('subtitle-box');
        const statusText = document.getElementById('status-text');
        const startBtn = document.getElementById('start-btn');
        
        let vapiInstance = null;
        let ws = null;

        async function initApp() {{
            try {{
                // 初始化 Vapi
                vapiInstance = new Vapi("{VAPI_PUBLIC_KEY}"); 
                
                // 激活按钮
                startBtn.disabled = false;
                startBtn.style.backgroundColor = "#00cc66"; [cite: 12]
                startBtn.style.cursor = "pointer";
                startBtn.innerText = "开始实时翻译";
                statusText.innerText = "✅ 系统已就绪";

                // WebSocket 连接逻辑 [cite: 14]
                function connectWS() {{
                    ws = new WebSocket("{WSS_URL}");
                    ws.onopen = () => {{ statusText.innerText = "✅ 已连接到翻译服务器"; }};
                    ws.onmessage = (e) => {{
                        const data = JSON.parse(e.data);
                        if (data.translation) {{
                            subtitleBox.innerHTML = "<div>" + data.translation + "</div>"; [cite: 14]
                        }}
                    }};
                    ws.onclose = () => setTimeout(connectWS, 3000); [cite: 15]
                }}
                connectWS();

                // 事件监听 [cite: 16]
                vapiInstance.on('call-start', () => {{
                    statusText.innerText = "🎙️ 正在监听对白...";
                    startBtn.innerText = "停止翻译";
                    startBtn.style.backgroundColor = "#ff4b4b"; [cite: 20]
                }});

                vapiInstance.on('call-end', () => {{
                    statusText.innerText = "✅ 已停止";
                    startBtn.innerText = "开始实时翻译";
                    startBtn.style.backgroundColor = "#00cc66";
                }});

                vapiInstance.on('error', (err) => {{
                    console.error("Vapi Error:", err);
                    statusText.innerText = "❌ 麦克风开启失败";
                }});

                startBtn.onclick = async () => {{
                    if (startBtn.innerText === "停止翻译") {{
                        vapiInstance.stop();
                    }} else {{
                        try {{
                            statusText.innerText = "正在请求麦克风...";
                            await vapiInstance.start("{VAPI_ASSISTANT_ID}"); [cite: 19]
                        }} catch (e) {{
                            alert("请确保在 HTTPS 环境下并允许麦克风权限");
                        }}
                    }}
                }};

            }} catch (err) {{
                statusText.innerText = "❌ 脚本加载失败，请检查网络";
                console.error(err);
            }}
        }}

        initApp();
    </script>
</body>
</html>
"""

# --- 4. 渲染 ---
# 必须显式开启 microphone 权限 
components.html(st_html, height=500, scrolling=False)