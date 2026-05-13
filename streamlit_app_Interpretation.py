import streamlit as st

st.set_page_config(page_title="Movie AI Translator", layout="centered")

# --- 1. 配置参数 ---
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"

st.title("🎬 电影同声传译 (AI)")

# --- 2. 注入 HTML/JS ---
# 使用 st.markdown 并启用 unsafe_allow_html 是绕过沙盒的唯一机会 [cite: 27]
st.markdown(f"""
<div style="background:#1a1a1a; padding:20px; border-radius:10px; border:1px solid #333;">
    <div id="sub-box" style="color:#ffcc00; min-height:100px; font-size:24px; text-align:center; margin-bottom:20px;">
        等待语音输入...
    </div>
    <button id="v-btn" style="width:100%; height:50px; background:#00cc66; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">
        ▶ 开始实时翻译
    </button>
    <p id="v-status" style="color:#888; text-align:center; margin-top:10px;">状态: 正在初始化...</p>
</div>

<script type="module">
    import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';
    
    const btn = document.getElementById('v-btn');
    const status = document.getElementById('v-status');
    const sub = document.getElementById('sub-box');

    try {{
        const vapi = new Vapi("{VAPI_PUBLIC_KEY}");
        status.innerText = "✅ 引擎就绪";

        vapi.on('call-start', () => {{
            status.innerText = "🎙️ 通话中...";
            btn.innerText = "⏹ 停止翻译";
            btn.style.background = "#ff4b4b";
        }});

        vapi.on('call-end', () => {{
            status.innerText = "✅ 已挂断";
            btn.innerText = "▶ 开始实时翻译";
            btn.style.background = "#00cc66";
        }});

        btn.onclick = async () => {{
            if (vapi.isCallActive()) {{
                vapi.stop();
            }} else {{
                status.innerText = "请求麦克风中...";
                await vapi.start("{VAPI_ASSISTANT_ID}");
            }}
        }};
    }} catch (e) {{
        status.innerText = "❌ 初始化失败: " + e.message;
    }}
</script>
""", unsafe_allow_html=True)