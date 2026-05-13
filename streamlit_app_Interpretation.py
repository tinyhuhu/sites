import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# 1. 配置区域（请确保这些 ID 与你控制台一致）
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
IOT_ENDPOINT = "a3pqsh1g7enzj8-ats.iot.us-east-2.amazonaws.com" 

# 2. 嵌入 JavaScript 逻辑
st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 100px;
font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; line-height: 1.5;">
    等待翻译中...
</div>

<button id="start-btn" style="width: 100%; height: 60px; background-color: #00cc66;
color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">开始实时翻译</button>

<script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js"></script>

<script type="module">
    // 使用 ESM 方式加载 Vapi，解决 "Vapi is not a constructor" 报错
    import VapiWeb from 'https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/+esm';

    const startBtn = document.getElementById('start-btn');
    const subtitleBox = document.getElementById('subtitle-box');
    
    // 初始化 Vapi
    const Vapi = typeof VapiWeb === 'function' ? VapiWeb : VapiWeb.default;
    const vapi = new Vapi("{VAPI_PUBLIC_KEY}");

    // --- 1. AWS IoT MQTT 逻辑 ---
    // 产生随机 ID 避免卡尔加里本地多设备连接冲突
    const clientId = "client_" + Math.random().toString(16).substr(2, 8);
    const client = new Paho.MQTT.Client("wss://" + "{IOT_ENDPOINT}" + "/mqtt", clientId);
    
    client.onMessageArrived = function(message) {{
        try {{
            const data = JSON.parse(message.payloadString);
            subtitleBox.innerHTML = `
                <div style="font-size: 16px; color: #888; margin-bottom: 8px;">原文: ${{data.original || "..."}}</div>
                <div style="color: #ffcc00;">${{data.translation || "正在翻译..."}}</div>
            `;
        }} catch (e) {{
            console.error("解析消息失败:", e);
        }}
    }};

    function connectMQTT() {{
        client.connect({{
            useSSL: true,
            timeout: 5,
            keepAliveInterval: 60,
            onSuccess: function() {{
                console.log("✅ MQTT 连接成功");
                client.subscribe("movie/subtitle");
            }},
            onFailure: function(err) {{
                console.log("❌ MQTT 连接失败，正在重试...");
                setTimeout(connectMQTT, 3000); 
            }}
        }});
    }}

    connectMQTT();

    // --- 2. Vapi 控制逻辑 ---
    startBtn.onclick = async () => {{
        if (startBtn.innerText === "开始实时翻译") {{
            try {{
                // 关键点：使用对象格式传递 assistantId 解决 400 错误
                await vapi.start({{ assistantId: "{VAPI_ASSISTANT_ID}" }});
                startBtn.innerText = "停止翻译";
                startBtn.style.backgroundColor = "#ff4444";
                subtitleBox.innerText = "正在聆听并翻译...";
            }} catch (err) {{
                console.error("Vapi 启动失败:", err);
                alert("启动失败，请检查浏览器麦克风权限");
            }}
        }} else {{
            vapi.stop();
            startBtn.innerText = "开始实时翻译";
            startBtn.style.backgroundColor = "#00cc66";
        }}
    }};
</script>
"""

components.html(st_html, height=550)