import streamlit as st

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

# --- 3. 构造注入的 HTML (使用单引号包裹 JS 内部字符串，避免与 Python 冲突) ---
injection_html = f"""
<div id="translator-container" style="background-color: #1a1a1a; padding: 25px; border-radius: 15px; border: 2px solid #333;">
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
            // 安全环境检查 
            if (!window.isSecureContext && window.location.hostname !== 'localhost') {{
                throw new Error('请使用 localhost 或 HTTPS 访问以开启麦克风权限');
            }}

            const vapi = new Vapi('{VAPI_PUBLIC_KEY}');
            
            // WebSocket 连接
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
                console.error(err);
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

# --- 4. 渲染 (确保使用 unsafe_allow_html=True) ---
st.markdown(injection_html, unsafe_allow_html=True) 

st.write("---")
st.caption("注：如果本地运行，请确保访问地址为 http://localhost:8501")