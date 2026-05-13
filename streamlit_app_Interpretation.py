import streamlit as st

# --- 1. 页面配置 ---
st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# --- 2. 配置区域 ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

# --- 3. 构造注入内容 ---
# 所有的 JS 大括号必须双写 {{ }} 以防 f-string 报错
st_content = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
    等待翻译中...
</div>
<button id="vapi-btn" style="width: 100%; height: 60px; background-color: #666; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: not-allowed; font-weight: bold;">
    正在加载 AI 引擎...
</button>
<p id="vapi-status" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">
    状态: 正在下载依赖库...
</p>

<script src="https://unpkg.com/@vapi-ai/web@2.5.2/dist/vapi.browser.js"></script>

<script>
(function() {{
    const subBox = document.getElementById('subtitle-box');
    const status = document.getElementById('vapi-status');
    const btn = document.getElementById('vapi-btn');
    
    let vInstance = null;
    let ws = null;

    // 轮询检查 SDK 是否加载完成
    const checkTimer = setInterval(() => {{
        if (window.Vapi) {{
            clearInterval(checkTimer);
            startInit();
        }}
    }}, 500);

    function startInit() {{
        try {{
            // 1. 初始化 Vapi
            vInstance = new window.Vapi("{VAPI_PUBLIC_KEY}");
            
            // 2. 激活按钮
            btn.disabled = false;
            btn.style.backgroundColor = "#00cc66";
            btn.style.cursor = "pointer";
            btn.innerText = "开始实时翻译";
            status.innerText = "✅ 设备已就绪";

            // 3. 建立 WebSocket (用于接收翻译)
            function connect() {{
                ws = new WebSocket("{WSS_URL}");
                ws.onopen = () => {{ status.innerText = "✅ 已连接到翻译后端"; }};
                ws.onmessage = (e) => {{
                    try {{
                        const data = JSON.parse(e.data);
                        if (data.translation) {{
                            subBox.innerHTML = '<div style="color:#ffcc00;">' + data.translation + '</div>';
                        }}
                    {{ catch (err) {{ console.error(err); }}
                }};
                ws.onclose = () => setTimeout(connect, 3000);
            }}
            connect();

            // 4. 事件绑定
            vInstance.on('call-start', () => {{
                status.innerText = "🎙️ 正在监听并翻译...";
                btn.innerText = "停止翻译";
                btn.style.backgroundColor = "#ff4b4b";
            }});

            vInstance.on('call-end', () => {{
                status.innerText = "✅ 已停止";
                btn.innerText = "开始实时翻译";
                btn.style.backgroundColor = "#00cc66";
            }});

            vInstance.on('error', (e) => {{
                console.error(e);
                status.innerText = "❌ 麦克风连接异常";
            }});

            // 5. 点击控制
            btn.onclick = async () => {{
                if (vInstance.isCallActive()) {{
                    vInstance.stop();
                }} else {{
                    try {{
                        status.innerText = "正在开启麦克风...";
                        await vInstance.start("{VAPI_ASSISTANT_ID}");
                    }} catch (err) {{
                        alert("麦克风启动失败，请确保使用 HTTPS 并授予权限。");
                    }}
                }}
            }};

        }} catch (err) {{
            status.innerText = "❌ 初始化失败: " + err.message;
        }}
    }}
}})();
</script>
"""

# --- 4. 注入渲染 ---
st.markdown(st_content, unsafe_allow_html=True)