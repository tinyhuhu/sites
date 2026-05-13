import streamlit as st

st.set_page_config(page_title="Movie AI Translator", layout="centered")

# --- 1. 配置 (保持不变) ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/"

st.title("🎬 电影同声传译 (AI)")

# --- 2. 注入逻辑 (核心：移除 components.html) ---
st.markdown(f"""
<div id="translator-ui" style="background: #1e1e1e; padding: 25px; border-radius: 15px; border: 1px solid #333;">
    <div id="subtitle-box" style="background: #000; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 100px; font-size: 22px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 1px solid #444;">
        等待语音输入...
    </div>
    <button id="v-btn" style="width: 100%; height: 60px; background: #00cc66; color: white; border: none; border-radius: 8px; font-size: 18px; cursor: pointer; font-weight: bold; transition: 0.3s;">
        ▶ 开始实时翻译
    </button>
    <p id="v-status" style="color: #888; font-size: 13px; text-align: center; margin-top: 15px;">
        系统状态: <span id="status-tag">准备就绪</span>
    </p>
</div>

<script type="module">
    import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

    const btn = document.getElementById('v-btn');
    const tag = document.getElementById('status-tag');
    const sub = document.getElementById('subtitle-box');

    // 1. 初始化引擎
    const vapi = new Vapi("{VAPI_PUBLIC_KEY}");
    tag.innerText = "✅ 引擎已就绪";

    // 2. WebSocket 翻译逻辑 [cite: 7]
    const ws = new WebSocket("{WSS_URL}");
    ws.onmessage = (e) => {{
        const data = JSON.parse(e.data);
        if (data.translation) sub.innerText = data.translation;
    }};

    // 3. Vapi 事件 [cite: 8, 9]
    vapi.on('call-start', () => {{
        tag.innerText = "🎙️ 正在通话中...";
        btn.innerText = "⏹ 停止翻译";
        btn.style.background = "#ff4b4b";
    }});

    vapi.on('call-end', () => {{
        tag.innerText = "✅ 已挂断";
        btn.innerText = "▶ 开始实时翻译";
        btn.style.background = "#00cc66";
    }});

    vapi.on('error', (e) => {{
        tag.innerText = "❌ 错误: " + (e.message || "权限被拒绝");
        console.error(e);
    }});

    // 4. 点击逻辑 (确保在最后绑定) [cite: 10, 11]
    btn.onclick = async () => {{
        if (vapi.isCallActive()) {{
            vapi.stop();
        }} else {{
            tag.innerText = "正在申请麦克风...";
            await vapi.start("{VAPI_ASSISTANT_ID}");
        }}
    }};
</script>
""", unsafe_allow_html=True)