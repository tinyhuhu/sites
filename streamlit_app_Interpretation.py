import streamlit as st

st.set_page_config(page_title="Movie AI Translator", layout="centered")

# --- 配置 (请再次确认 ID 是否正确) ---
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/"

st.title("🎬 电影同声传译 (AI)")

# 使用 st.markdown 注入 HTML 和脚本
# 注意：一定要把 unsafe_allow_html 设为 True
st.markdown(f"""
<div id="translator-ui" style="border: 1px solid #444; padding: 20px; border-radius: 15px;">
    <div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px;">
        等待翻译中...
    </div>
    <button id="v-action-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">
        开始实时翻译
    </button>
    <p id="v-status" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">连接状态: 等待操作...</p>
</div>

<script type="module">
    import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2';

    const subBox = document.getElementById('subtitle-box');
    const status = document.getElementById('v-status');
    const btn = document.getElementById('v-action-btn');
    
    // 初始化 Vapi
    const vapi = new Vapi("{VAPI_PUBLIC_KEY}");
    console.log("Vapi Object Created");
    status.innerText = "✅ 引擎加载成功";

    // WebSocket 处理翻译显示 [cite: 21]
    let ws = new WebSocket("{WSS_URL}");
    ws.onmessage = (e) => {{
        const data = JSON.parse(e.data);
        if (data.translation) {{
            subBox.innerHTML = '<div style="color:#ffcc00;">' + data.translation + '</div>';
        }}
    }};

    // 监听 Vapi 事件 [cite: 22, 23]
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
        status.innerText = "❌ 错误: " + (err.message || "环境限制");
    }});

    // 按钮点击逻辑 [cite: 24, 25, 26]
    btn.onclick = async () => {{
        if (btn.innerText.includes("开始")) {{
            status.innerText = "正在唤起麦克风...";
            try {{
                await vapi.start("{VAPI_ASSISTANT_ID}");
            }} catch (e) {{
                status.innerText = "❌ 启动失败: " + e.message;
            }}
        }} else {{
            vapi.stop();
        }}
    }};
</script>
""", unsafe_allow_html=True)