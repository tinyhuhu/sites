import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# 1. 配置区域
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
IOT_ENDPOINT = "a3pqsh1g7enzj8-ats.iot.us-east-2.amazonaws.com" 

# 2. 嵌入修复后的 JavaScript 逻辑 [cite: 9]
st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px;
font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
    等待翻译中...
</div>

<button id="start-btn" style="width: 100%; height: 60px; background-color: #00cc66;
color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">开始实时翻译</button>

<p id="status-text" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">连接状态: 检查中...</p>

<script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js"></script>

<script type="module">
    // 使用 ESM 方式加载 Vapi 以避免 "not a constructor" 错误 [cite: 7]
    import VapiWeb from 'https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/+esm';

    const startBtn = document.getElementById('start-btn');
    const subtitleBox = document.getElementById('subtitle-box');
    const statusText = document.getElementById('status-text');
    
    const Vapi = typeof VapiWeb === 'function' ? VapiWeb : VapiWeb.default;
    const vapi = new Vapi("{VAPI_PUBLIC_KEY}");

    // --- 1. AWS IoT MQTT 增强版逻辑 ---
    // 生成唯一 ClientID 避免冲突 [cite: 12]
    const clientId = "interpreter_" + Math.random().toString(16).substr(2, 8);
    const client = new Paho.MQTT.Client("wss://" + "{IOT_ENDPOINT}" + "/mqtt", clientId);
    
    client.onMessageArrived = function(message) {{
        try {{
            const data = JSON.parse(message.payloadString);
            subtitleBox.innerHTML = `
                <div style="font-size: 16px; color: #aaa; margin-bottom: 10px;">原文: ${{data.original || "..."}}</div>
                <div style="color: #ffcc00; font-size: 28px;">${{data.translation || "正在翻译..."}}</div>
            `; [cite: 13, 14]
        }} catch (e) {{ console.error("解析失败", e); }}
    }};

    function connectMQTT() {{
        statusText.innerText = "正在尝试连接 AWS IoT...";
        client.connect({{
            useSSL: true,
            timeout: 10,
            keepAliveInterval: 60,
            onSuccess: function() {{
                statusText.innerText = "✅ 已成功连接到 AWS IoT";
                statusText.style.color = "#00cc66";
                client.subscribe("movie/subtitle");
            }},
            onFailure: function(err) {{
                statusText.innerText = "❌ MQTT 连接失败，可能是策略未关联，正在重试...";
                statusText.style.color = "#ff4444";
                setTimeout(connectMQTT, 5000); 
            }}
        }});
    }}

    connectMQTT();

    // --- 2. Vapi 控制逻辑 ---
    startBtn.onclick = async () => {{
        if (startBtn.innerText === "开始实时翻译") {{
            try {{
                // 关键点：使用对象格式传递 assistantId 彻底解决 400 错误 
                await vapi.start({{
                    assistantId: "{VAPI_ASSISTANT_ID}"
                }});
                startBtn.innerText = "停止翻译";
                startBtn.style.backgroundColor = "#ff4444";
                subtitleBox.innerText = "正在聆听并翻译...";
            }} catch (err) {{
                console.error("Vapi Error:", err);
                alert("启动失败，请确保已授予浏览器麦克风权限。");
            }}
        }} else {{
            vapi.stop();
            startBtn.innerText = "开始实时翻译";
            startBtn.style.backgroundColor = "#00cc66";
            subtitleBox.innerText = "等待翻译中..."; [cite: 16]
        }}
    }};
</script>
"""

components.html(st_html, height=600)