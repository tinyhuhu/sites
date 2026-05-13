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
# 核心改变：直接注入 HTML 结构，不使用 components.html
st_content = f"""
<div id="translator-container">
    <div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
        等待翻译中...
    </div>
    <button id="vapi-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">
        开始实时翻译
    </button>
    <p id="vapi-status" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">
        连接状态: 正在初始化引擎...
    </p>
</div>

<script>
(async () => {{
    // 动态导入，确保在 Calgary 环境下使用你确认可用的 esm.sh
    const {{ default: Vapi }} = await import('https://esm.sh/@vapi-ai/web@2.5.2');
    
    const subBox = document.getElementById('subtitle-box');
    const status = document.getElementById('vapi-status');
    const btn = document.getElementById('vapi-btn');
    
    let vInstance = null;
    let ws = null;

    try {{
        vInstance = new Vapi("{VAPI_PUBLIC_KEY}");
        status.innerText = "✅ 引擎加载成功";

        // WebSocket 连接 (处理来自 Lambda 的翻译文本)
        const connectWS = () => {{
            ws = new WebSocket("{WSS_URL}");
            ws.onopen = () => {{ status.innerText = "✅ 已连接到翻译服务器"; }};
            ws.onmessage = (e) => {{
                const data = JSON.parse(e.data);
                if (data.translation) {{
                    subBox.innerHTML = '<div style="color:#ffcc00;">' + data.translation + '</div>';
                }}
            }};
            ws.onclose = () => setTimeout(connectWS, 3000);
        }};
        connectWS();

        // 监听 Vapi 事件
        vInstance.on('call-start', () => {{
            status.innerText = "🎙️ 正在监听对白并实时翻译...";
            btn.innerText = "停止翻译";
            btn.style.backgroundColor = "#ff4b4b";
        }});

        vInstance.on('call-end', () => {{
            status.innerText = "✅ 已停止";
            btn.innerText = "开始实时翻译";
            btn.style.backgroundColor = "#00cc66";
        }});

        vInstance.on('error', (e) => {{
            console.error("Vapi SDK Error:", e);
            status.innerText = "❌ 麦克风或呼叫异常，请检查权限";
        }});

        // 按钮交互逻辑
        btn.onclick = async () => {{
            if (btn.innerText === "停止翻译") {{
                vInstance.stop();
            }} else {{
                try {{
                    status.innerText = "正在请求麦克风...";
                    await vInstance.start("{VAPI_ASSISTANT_ID}");
                }} catch (err) {{
                    console.error(err);
                    alert("启动失败。请检查浏览器地址栏左侧的麦克风权限。");
                }}
            }}
        }};
    }} catch (err) {{
        status.innerText = "❌ 引擎初始化失败: " + err.message;
    }}
}})();
</script>
"""

# --- 4. 关键：使用 st.markdown 进行主页面注入 ---
# 这样 JS 就在主域运行，不再有 Origin 'null' 的报错
st.markdown(st_content, unsafe_allow_html=True)