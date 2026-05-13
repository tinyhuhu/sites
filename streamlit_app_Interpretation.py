import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# 1. 配置区域
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
IOT_ENDPOINT = "a3pqsh1g7enzj8-ats.iot.us-east-2.amazonaws.com" 

# 2. 嵌入 JavaScript 代码
st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 100px;
font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px;">
    等待翻译中...
</div>

<button id="start-btn" style="width: 100%; height: 50px; background-color: #00cc66;
color: white; border: none; border-radius: 5px; font-size: 18px;">开始实时翻译</button>

<script src="https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/dist/vapi.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js"></script>

<script>
    window.onload = () => {{
        // 检查 SDK 是否成功挂载到全局
        if (typeof Vapi !== 'undefined') {{
            const vapi = new Vapi("{VAPI_PUBLIC_KEY}");
            const startBtn = document.getElementById('start-btn');
            const subtitleBox = document.getElementById('subtitle-box');

            // --- 1. AWS IoT MQTT 设置 ---
            const client = new Paho.MQTT.Client("wss://" + "{IOT_ENDPOINT}" + "/mqtt", "clientId-" + Math.random());
            
            client.onMessageArrived = function(message) {{
                try {{
                    const data = JSON.parse(message.payloadString);
                    subtitleBox.innerHTML = `
                        <div style="font-size: 16px; color: #888; margin-bottom: 5px;">${{data.original}}</div>
                        <div>${{data.translation}}</div>
                    `;
                }} catch (e) {{
                    console.error("解析消息失败:", e);
                }}
            }};

            client.connect({{
                useSSL: true,
                timeout: 3,
                onSuccess: function() {{
                    client.subscribe("movie/subtitle");
                    console.log("MQTT 连接成功");
                }},
                onFailure: function(err) {{
                    console.error("MQTT 连接失败:", err);
                }}
            }});

            // --- 2. Vapi 控制 ---
            startBtn.onclick = () => {{
                if (startBtn.innerText === "开始实时翻译") {{
                    vapi.start("{VAPI_ASSISTANT_ID}");
                    startBtn.innerText = "停止";
                    startBtn.style.backgroundColor = "#ff4444";
                }} else {{
                    vapi.stop();
                    startBtn.innerText = "开始实时翻译";
                    startBtn.style.backgroundColor = "#00cc66";
                }}
            }};
        }} else {{
            document.getElementById('subtitle-box').innerText = "SDK 加载失败，请检查网络或更换 CDN。";
        }}
    }};
</script>
"""

components.html(st_html, height=500)