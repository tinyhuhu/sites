import streamlit as st

# --- 1. 配置 ---
st.set_page_config(page_title="Movie AI Translator", layout="centered")
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

st.title("🎬 电影同声传译 (AI)")

# --- 2. 注入 HTML/JS (不再使用 components.html) ---
# 注意：这里改用 st.markdown 以直接在主域运行 JS
injection_html = f"""
<div id="translator-ui">
    <div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
        等待翻译中...
    </div>
    <button id="v-action-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">开始实时翻译</button>
    <p id="v-status" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">连接状态: 正在加载引擎...</p>
</div>

<script type="module">
    // 动态导入，确保跳出沙盒运行
    import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

    const subBox = document.getElementById('subtitle-box');
    const status = document.getElementById('v-status');
    const btn = document.getElementById('v-action-btn');
    
    try {{
        const vapi = new Vapi("{VAPI_PUBLIC_KEY}");
        status.innerText = "✅ 引擎初始化成功";

        // WebSocket 逻辑 [cite: 19, 20]
        let ws = new WebSocket("{WSS_URL}");
        ws.onmessage = (e) => {{
            const data = JSON.parse(e.data);
            if (data.translation) subBox.innerHTML = '<div style="color:#ffcc00;">' + data.translation + '</div>';
        }};

        // Vapi 事件监听 [cite: 21, 23]
        vapi.on('call-start', () => {{
            status.innerText = "🎙️ 正在监听翻译...";
            btn.innerText = "停止翻译";
            btn.style.backgroundColor = "#ff4b4b";
        }});

        vapi.on('call-end', () => {{
            status.innerText = "✅ 已结束";
            btn.innerText = "开始实时翻译";
            btn.style.backgroundColor = "#00cc66";
        }});

        vapi.on('error', (err) => {{
            console.error("Vapi Error:", err);
            status.innerText = "❌ 错误: " + (err.message || "麦克风权限不足");
        }});

        // 按钮点击逻辑 [cite: 25]
        btn.onclick = async () => {{
            if (btn.innerText === "停止翻译") {{
                vapi.stop();
            }} else {{
                status.innerText = "正在唤起麦克风...";
                await vapi.start("{VAPI_ASSISTANT_ID}");
            }}
        }};
    }} catch (e) {{
        status.innerText = "❌ 初始化失败: " + e.message;
        console.error(e);
    }}
</script>
"""

# 核心：使用 markdown 注入，绕过 Iframe [cite: 15, 27]
st.markdown(injection_html, unsafe_allow_html=True)