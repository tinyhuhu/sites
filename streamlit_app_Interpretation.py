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

# --- 3. 构造注入的 HTML ---
# 使用 unsafe_allow_html 时，脚本会直接运行在主页面，通常能绕过 iframe 的权限限制
injection_html = f"""
<div id="translator-root" style="background-color: #1a1a1a; padding: 25px; border-radius: 15px; border: 2px solid #333; margin-bottom: 20px;">
    <div id="subtitle-box" style="color: #ffcc00; min-height: 120px; font-size: 26px; font-weight: bold; text-align: center; margin-bottom: 25px; display: flex; align-items: center; justify-content: center; line-height: 1.4;">
        等待语音输入...
    </div>
    
    <button id="v-action-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 10px; font-size: 20px; cursor: pointer; font-weight: bold; transition: 0.3s;">
        开始实时翻译
    </button>
    
    <p id="v-status" style="color: #888; font-size: 14px; text-align: center; margin-top: 15px;">
        状态: 正在初始化引擎...
    </p>
</div>

<script type="module">
    // 使用动态 import 确保在主页面环境加载
    import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

    const subBox = document.getElementById('subtitle-box');
    const status = document.getElementById('v-status');
    const btn = document.getElementById('v-action-btn');

    let vapiInstance = null;

    async function initApp() {{
        try {{
            vapiInstance = new Vapi('{VAPI_PUBLIC_KEY}');
            
            const ws = new WebSocket('{WSS_URL}');
            ws.onmessage = (e) => {{
                try {{
                    const data = JSON.parse(e.data);
                    if (data.translation) subBox.innerText = data.translation;
                }} catch(err) {{ console.error("WS解析错误", err); }}
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

            vapiInstance.on('error', (err) => {{
                status.innerText = '❌ 错误: ' + (err.message || '麦克风权限被拒绝');
                console.error("Vapi Error:", err);
            }});

            status.innerText = '✅ 引擎已就绪';

            btn.onclick = async () => {{
                if (vapiInstance.isCallActive()) {{
                    vapiInstance.stop();
                }} else {{
                    status.innerText = '正在请求麦克风权限...';
                    try {{
                        await vapiInstance.start('{VAPI_ASSISTANT_ID}');
                    }} catch (e) {{
                        status.innerText = '⚠️ 权限请求失败';
                        console.error(e);
                    }}
                }}
            }};
        }} catch (e) {{
            status.innerText = '⚠️ 无法初始化: ' + e.message;
            console.error("Initialization Error:", e);
        }}
    }}

    // 延迟执行确保 DOM 加载完毕
    setTimeout(initApp, 500);
</script>
"""

# --- 4. 渲染 ---
st.markdown(injection_html, unsafe_allow_html=True)

st.write("---")
st.caption("注：本地运行时请通过 http://localhost:8501 访问。如果依然无法点击，请检查 F12 Console 报错。")