import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Movie AI Translator", layout="centered")

st.title("🎬 电影同声传译 (AI)")
st.info("手机请靠近音箱，点击开始后将实时显示中文翻译。")

# 1. 配置区域
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85"
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6"
IOT_ENDPOINT = "a3pqsh1g7enzj8-ats.iot.us-east-2.amazonaws.com" 

# 2. 嵌入修复后的 JavaScript 逻辑
# 注意：这里使用了 f"""..."""，因此代码内部所有的 JS 大括号都已转义为 {{ }}
st_html = f"""
<div id="subtitle-box" style="background-color: #1a1a1a; color: #ffcc00; padding: 20px; border-radius: 10px; min-height: 120px; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; border: 2px solid #333;">
    等待翻译中...
</div>
<button id="start-btn" style="width: 100%; height: 60px; background-color: #00cc66; color: white; border: none; border-radius: 8px; font-size: 20px; cursor: pointer; font-weight: bold;">开始实时翻译</button>
<p id="status-text" style="color: #888; font-size: 14px; text-align: center; margin-top: 10px;">连接状态: 准备中...</p>

<script src="https://cdnjs.cloudflare.com/ajax/libs/aws-sdk/2.1289.0/aws-sdk.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/paho-mqtt/1.0.1/mqttws31.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/crypto-js@4.1.1/crypto-js.js"></script>

<script type="module">
    import VapiWeb from 'https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/+esm';
    
    // --- 核心配置 ---
    const REGION = "us-east-2";
    const IOT_ENDPOINT = "{IOT_ENDPOINT}"; 
    const IDENTITY_POOL_ID = "us-east-2:f82a3d3f-5561-4f43-a0c3-cd87075e477e"; // 请填入您刚才创建后获得的 ID
    
    const subtitleBox = document.getElementById('subtitle-box');
    const statusText = document.getElementById('status-text');

    // 1. 初始化 AWS 凭证
    AWS.config.region = REGION;
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({{
        IdentityPoolId: IDENTITY_POOL_ID
    }});

    // 2. 生成 SigV4 签名 URL (这是最关键的逻辑)
    function getSignedUrl(endpoint, region, credentials) {{
        const time = new Date().toISOString().replace(/[:\-]|\.\d{{3}}/g, '');
        const date = time.substr(0, 8);
        const method = 'GET';
        const service = 'iotdevicegateway';
        const host = endpoint.toLowerCase();
        const path = '/mqtt';
        
        // 在构建 queryParams 数组时
        const queryParams = [
            'X-Amz-Algorithm=AWS4-HMAC-SHA256',
            'X-Amz-Credential=' + encodeURIComponent(credentials.accessKeyId + '/' + date + '/' + region + '/' + service + '/aws4_request'),
            'X-Amz-Date=' + time,
            'X-Amz-SignedHeaders=host'
        ];

        // !!! 必须加入这一段，否则 403 报错 !!!
        if (credentials.sessionToken) {{
            queryParams.push('X-Amz-Security-Token=' + encodeURIComponent(credentials.sessionToken));
        }}
        
        const canonicalQuerystring = queryParams.sort().join('&');
        const canonicalRequest = method + '\\n' + path + '\\n' + canonicalQuerystring + '\\n' + 'host:' + host + '\\n\\n' + 'host' + '\\n' + CryptoJS.SHA256('').toString();
        const stringToSign = 'AWS4-HMAC-SHA256\\n' + time + '\\n' + date + '/' + region + '/' + service + '/aws4_request\\n' + CryptoJS.SHA256(canonicalRequest).toString();
        
        function kHMAC(key, data) {{ return CryptoJS.HmacSHA256(data, key); }}
        const kDate = kHMAC('AWS4' + credentials.secretAccessKey, date);
        const kRegion = kHMAC(kDate, region);
        const kService = kHMAC(kRegion, service);
        const kSigning = kHMAC(kService, 'aws4_request');
        const signature = kHMAC(kSigning, stringToSign).toString();
        
        return 'wss://' + host + path + '?' + canonicalQuerystring + '&X-Amz-Signature=' + signature;
    }}

    // 3. 执行连接
    function connectMQTT() {{
        statusText.innerText = "获取 AWS 身份中...";
        
        AWS.config.credentials.get((err) => {{
            if (err) {{
                statusText.innerText = "❌ 身份获取失败: " + err.message;
                return;
            }}

            const signedUrl = getSignedUrl(IOT_ENDPOINT, REGION, AWS.config.credentials);
            console.log('signedURL is: ' + signedUrl)
            const clientId = 'client-' + Math.random().toString(16).substr(2, 8);
            const client = new Paho.MQTT.Client(signedUrl, clientId);

            client.onMessageArrived = (msg) => {{
                const data = JSON.parse(msg.payloadString);
                subtitleBox.innerHTML = `<div style="color:#ffcc00;">${{data.translation}}</div>`;
            }};

            client.connect({{
                useSSL: true,
                onSuccess: () => {{
                    statusText.innerText = "✅ 已通过 Cognito 连接";
                    statusText.style.color = "#00cc66";
                    client.subscribe("movie/subtitle");
                }},
                onFailure: (e) => {{
                    statusText.innerText = "❌ 连接失败，请检查 IAM 角色是否挂载了内联策略";
                    console.error(e);
                }}
            }});
        }});
    }}

    connectMQTT();
    // ... Vapi 逻辑保持不变 ...
</script>
"""

components.html(st_html, height=600)