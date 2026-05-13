import streamlit as st
import streamlit.components.v1 as components

# --- 1. 页面配置 ---
st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# --- 2. 配置区域 ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

# --- 3. 构造嵌入的 HTML/JS ---
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
            width: 100%; height: 60px; background-color: #00cc66; color: white;
            border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;
        }}
        #status-text {{ color: #888; font-size: 14px; text-align: center; margin-top: 10px; }}
    </style>
</head>
<body>
    <div id="subtitle-box">等待翻译中...</div>
    <button id="start-btn">开始实时翻译</button>
    <p id="status-text">连接状态: 正在加载引擎...</p>

    <script type="module">
        import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

        const subtitleBox = document.getElementById('subtitle-box');
        const statusText = document.getElementById('status-text');
        const startBtn = document.getElementById('start-btn');
        
        const vapi = new Vapi("{VAPI_PUBLIC_KEY}");
        let ws = null;

        // WebSocket 连接
        function connectWS() {{
            ws = new WebSocket("{WSS_URL}");
            ws.onopen = () => {{ statusText.innerText = "✅ 已连接到翻译服务器"; }};
            ws.onmessage = (e) => {{
                try {{
                    const data = JSON.parse(e.data);
                    if (data.translation) {{
                        subtitleBox.innerHTML = "<div>" + data.translation + "</div>";
                    }}
                }} catch (err) {{ console.error(err); }}
            }};
            ws.onclose = () => setTimeout(connectWS, 3000);
        }}
        connectWS();

        // Vapi 事件绑定
        vapi.on('call-start', () => {{
            statusText.innerText = "🎙️ 正在监听电影对白...";
            startBtn.innerText = "停止翻译";
            startBtn.style.backgroundColor = "#ff4b4b";
        }});

        vapi.on('call-end', () => {{
            statusText.innerText = "✅ 已停止";
            startBtn.innerText = "开始实时翻译";
            startBtn.style.backgroundColor = "#00cc66";
        }});

        vapi.on('error', (e) => {{
            console.error("Vapi Error Details:", e);
            statusText.innerText = "❌ 引擎错误: " + (e.message || "麦克风初始化失败");
        }});

        // 按钮交互
        startBtn.onclick = async () => {{
            if (startBtn.innerText === "停止翻译") {{
                vapi.stop();
            }} else {{
                try {{
                    statusText.innerText = "正在请求麦克风权限...";
                    // 核心调用
                    await vapi.start("{VAPI_ASSISTANT_ID}");
                }} catch (err) {{
                    console.error("Call Start Failed:", err);
                    alert("无法启动。请确保使用 HTTPS 访问，并检查浏览器是否允许该站点的麦克风权限。");
                }}
            }}
        }};
        
        statusText.innerText = "✅ 系统就绪";
    </script>
</body>
</html>
"""

# --- 4. 最终渲染 (核心修复点) ---
# 必须带上 allow="microphone" 参数，否则 iframe 会静默拦截麦克风请求
components.html(st_html, height=500, scrolling=False, allow="microphone")