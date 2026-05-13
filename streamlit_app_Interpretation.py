import streamlit as st

# --- 1. 页面配置 ---
st.set_page_config(
    page_title="Movie AI Translator",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. 核心配置参数 ---
# 请确保这两个 ID 是准确的
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
# WebSocket 地址用于接收翻译文本
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/"

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# --- 3. 注入增强版 HTML/JS ---
# 使用 st.markdown 直接注入，并增加了详细的错误捕获逻辑
injection_html = f"""
<div id="translator-container" style="background-color: #1a1a1a; padding: 25px; border-radius: 15px; border: 2px solid #333; box-shadow: 0 4px 15px rgba(0,0,0,0.5);">
    <div id="subtitle-box" style="color: #ffcc00; min-height: 120px; font-size: 26px; font-weight: bold; text-align: center; margin-bottom: 25px; display: flex; align-items: center; justify-content: center; line-height: 1.4;">
        等待翻译中...
    </div>
    
    <button id="v-action-btn" style="width: 100%; height: 65px; background-color: #00cc66; color: white; border: none; border-radius: 10px; font-size: 22px; cursor: pointer; font-weight: bold; transition: all 0.3s ease;">
        开始实时翻译
    </button>
    
    <p id="v-status" style="color: #888; font-size: 15px; text-align: center; margin-top: 15px; font-family: sans-serif;">
        状态: 正在检查系统环境...
    </p>
</div>

<script type="module">
    // 动态导入 Vapi SDK
    import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

    const subBox = document.getElementById('subtitle-box');
    const status = document.getElementById('v-status');
    const btn = document.getElementById('v-action-btn');

    let vapi = null;
    let ws = null;

    // 初始化函数
    async function initSystem() {{
        try {{
            // 1. 环境检查：必须是 localhost 或 HTTPS 才能调用麦克风
            if (!window.isSecureContext) {{
                throw new Error("环境安全校验失败：请使用 localhost 或 HTTPS 访问，否则浏览器将禁用麦克风。");
            }}

            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                throw new Error("浏览器限制：无法获取麦克风组件，请检查权限设置。");
            }}

            // 2. 实例化 Vapi
            vapi = new Vapi("{VAPI_PUBLIC_KEY}");
            
            // 3. 建立 WebSocket 连接
            ws = new WebSocket("{WSS_URL}");
            
            ws.onmessage = (e) => {{
                try {{
                    const data = JSON.parse(e.data);
                    if (data.translation) {{
                        subBox.innerHTML = `<span style="color:#ffcc00;">${{data.translation}}</span>`;
                    }}
                }} catch(err) {{ console.error("WS数据解析失败", err); }}
            }};

            ws.onerror = () => {{ status.innerText = "⚠️ WebSocket 翻译通道连接失败"; }};

            // 4. Vapi 事件监听
            vapi.on('call-start', () => {{
                status.innerText = "🎙️ 正在监听并翻译...";
                btn.innerText = "停止翻译";
                btn.style.backgroundColor = "#ff4b4b";
            }});

            vapi.on('call-end', () => {{
                status.innerText = "✅ 已挂断";
                btn.innerText = "开始实时翻译";
                btn.style.backgroundColor = "#00cc66";
            }});

            vapi.on('error', (err) => {{
                console.error("Vapi 运行时错误:", err);
                status.innerText = "❌ 运行时错误: " + (err.message || "麦克风被占用或权限不足");
                status.style.color = "#ff4b4b";
            }});

            status.innerText = "✅ 引擎就绪 (等待操作)";

            // 5. 绑定点击事件
            btn.onclick = async () => {{
                try {{
                    if (vapi.isCallActive()) {{
                        vapi.stop();
                    }} else {{
                        status.innerText = "正在请求麦克风权限...";
                        await vapi.start("{VAPI_ASSISTANT_ID}");
                    }}
                }} catch (err) {{
                    status.innerText = "❌ 启动失败: " + err.message;
                }}
            }};

        }} catch (e) {{
            status.innerText = "⚠️ 初始化失败: " + e.message;
            status.style.color = "#ff4b4b";
            btn.disabled = true;
            btn.style.opacity = "0.5";
            btn.style.cursor = "not-allowed";
            console.error("Initialization Error:", e);
        }}
    }}

    // 页面加载完成后启动初始化
    window.addEventListener('load', initSystem);
</script>
"""

# 注入代码
st.markdown(injection_html, unsafe_allow_html=True)

# --- 4. 底部补充说明 ---
st.write("---")
st.caption("技术栈: Streamlit + Vapi Web SDK + WebSocket 实时翻译层")