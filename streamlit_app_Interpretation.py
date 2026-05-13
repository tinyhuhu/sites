import streamlit as st
import streamlit.components.v1 as components

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="Movie AI Translator",
    layout="centered"
)

# --- 2. 参数配置 ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/"

st.title("🎬 电影同声传译 (AI)")

# --- 3. 构造纯净的 HTML 字符串 ---
# 将 JS 放在最下面，CSS 放在最上面，完全模拟一个独立的网页
custom_html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ background-color: #0e1117; color: white; font-family: sans-serif; }}
        .container {{
            background-color: #1a1a1a; 
            padding: 30px; 
            border-radius: 15px; 
            border: 1px solid #333;
            text-align: center;
        }}
        #subtitle-box {{
            color: #ffcc00; 
            min-height: 100px; 
            font-size: 24px; 
            font-weight: bold; 
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        #v-action-btn {{
            width: 100%; 
            height: 55px; 
            background-color: #00cc66; 
            color: white; 
            border: none; 
            border-radius: 8px; 
            font-size: 18px; 
            font-weight: bold;
            cursor: pointer;
        }}
        #v-status {{ color: #888; font-size: 13px; margin-top: 15px; }}
    </style>
</head>
<body>
    <div class="container">
        <div id="subtitle-box">等待语音输入...</div>
        <button id="v-action-btn">开始实时翻译</button>
        <p id="v-status">状态: 引擎初始化中...</p>
    </div>

    <script type="module">
        import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

        const subBox = document.getElementById('subtitle-box');
        const status = document.getElementById('v-status');
        const btn = document.getElementById('v-action-btn');

        let vapiInstance = null;

        async function init() {{
            try {{
                vapiInstance = new Vapi('{VAPI_PUBLIC_KEY}');
                
                // WebSocket 处理翻译显示
                const ws = new WebSocket('{WSS_URL}');
                ws.onmessage = (e) => {{
                    const data = JSON.parse(e.data);
                    if (data.translation) subBox.innerText = data.translation;
                }};

                vapiInstance.on('call-start', () => {{
                    status.innerText = '🎙️ 正在录音翻译...';
                    btn.innerText = '停止翻译';
                    btn.style.backgroundColor = '#ff4b4b';
                }});

                vapiInstance.on('call-end', () => {{
                    status.innerText = '✅ 已结束';
                    btn.innerText = '开始实时翻译';
                    btn.style.backgroundColor = '#00cc66';
                }});

                status.innerText = '✅ 引擎已就绪';

                btn.onclick = async () => {{
                    if (vapiInstance.isCallActive()) {{
                        vapiInstance.stop();
                    }} else {{
                        status.innerText = '正在请求麦克风...';
                        await vapiInstance.start('{VAPI_ASSISTANT_ID}');
                    }}
                }};
            }} catch (e) {{
                status.innerText = '❌ 初始化失败: ' + e.message;
            }}
        }}
        init();
    </script>
</body>
</html>
"""

# --- 4. 关键：使用 components.html 并显式赋予权限 ---
components.html(
    custom_html,
    height=320,
    scrolling=False,
    # 这一行是解决“点不动”的核心，它授权 iframe 使用麦克风
    allow="microphone"
)

st.info("💡 提示：如果按钮点击后没反应，请检查浏览器地址栏右侧是否拦截了麦克风权限。")