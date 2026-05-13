import streamlit as st
import streamlit.components.v1 as components  # 1. 导入组件模块

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="Movie AI Translator",
    layout="centered"
)

# --- 2. 核心参数 ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/"

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# --- 3. 构造注入的 HTML ---
# 注意：这里去掉了多余的 Python 注释，确保字符串纯净
injection_html = f"""
<div id="translator-container" style="background-color: #1a1a1a; padding: 25px; border-radius: 15px; border: 2px solid #333; font-family: sans-serif;">
    <div id="subtitle-box" style="color: #ffcc00; min-height: 120px; font-size: 26px; font-weight: bold; text-align: center; margin-bottom: 25px; display: flex; align-items: center; justify-content: center;">
        等待语音输入...
    </div>
    <button id="v-action-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 10px; font-size: 20px; cursor: pointer; font-weight: bold;">
        开始实时翻译
    </button>
    <p id="v-status" style="color: #888; font-size: 14px; text-align: center; margin-top: 15px;">
        状态: 正在初始化引擎...
    </p>
</div>

<script type="module">
    import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

    const subBox = document.getElementById('subtitle-box');
    const status = document.getElementById('v-status');
    const btn = document.getElementById('v-action-btn');

    async function startApp() {{
        try {{
            const vapi = new Vapi('{VAPI_PUBLIC_KEY}');
            const ws = new WebSocket('{WSS_URL}');

            ws.onmessage = (e) => {{
                const data = JSON.parse(e.data);
                if (data.translation) subBox.innerText = data.translation;
            }};

            vapi.on('call-start', () => {{
                status.innerText = '🎙️ 正在录音翻译...';
                btn.innerText = '停止翻译';
                btn.style.backgroundColor = '#ff4b4b';
            }});

            vapi.on('call-end', () => {{
                status.innerText = '✅ 已结束';
                btn.innerText = '开始实时翻译';
                btn.style.backgroundColor = '#00cc66';
            }});

            vapi.on('error', (err) => {{
                status.innerText = '❌ 错误: ' + (err.message || '麦克风调用失败');
            }});

            status.innerText = '✅ 引擎已就绪';

            btn.onclick = async () => {{
                if (vapi.isCallActive()) {{
                    vapi.stop();
                }} else {{
                    status.innerText = '请求权限中...';
                    await vapi.start('{VAPI_ASSISTANT_ID}');
                }}
            }};
        }} catch (e) {{
            status.innerText = '⚠️ 无法启动: ' + e.message;
            status.style.color = '#ff4b4b';
        }}
    }}
    startApp();
</script>
"""

# --- 4. 使用组件渲染 (关键修改) ---
# height 参数需要根据内容高度手动调整
components.html(
    injection_html, 
    height=350, 
    # 必须显式允许麦克风权限，否则 JavaScript 无法激活 Vapi 引擎
    allow="microphone" 
)

st.write("---")
st.caption("注：请确保通过 HTTPS 或 localhost 访问以获得麦克风权限。")