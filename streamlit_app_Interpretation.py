import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="Movie AI Translator",
    layout="centered"
)

# ===== 配置 =====
VAPI_ASSISTANT_ID = "585b5b56-9e7b-4c41-b369-693ce3256f85" 
VAPI_PUBLIC_KEY = "5f372b2b-5f3d-41b7-bd61-1522a5c35ff6" 
WSS_URL = "wss://un1qwkapg1.execute-api.us-east-2.amazonaws.com/production/" 

st.title("🎬 电影同声传译 (AI)") 

html_code = """
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#1a1a1a;">
<div style="padding:20px;border-radius:10px;border:1px solid #333;text-align:center;font-family:Arial;">
    <div id="subtitle-display" style="color:#ffcc00;min-height:80px;font-size:22px;font-weight:bold;margin-bottom:20px;">
        等待语音输入...
    </div>
    <button id="v-btn" style="width:100%;height:50px;background:#00cc66;color:white;border:none;border-radius:5px;font-size:18px;cursor:pointer;">
        开始实时翻译
    </button>
    <p id="v-msg" style="color:#888;font-size:12px;margin-top:10px;">
        状态: 初始化中...
    </p>
</div>

<script type="module">
import Vapi from 'https://esm.sh/@vapi-ai/web@2.5.2'; 

const display = document.getElementById('subtitle-display');
const msg = document.getElementById('v-msg');
const btn = document.getElementById('v-btn');

let vapi = null;

try {
    vapi = new Vapi('__PUBLIC_KEY__'); 
    msg.innerText = '✅ Vapi 已加载'; 
} catch(err) {
    msg.innerText = '❌ Vapi 加载失败'; 
    console.error(err);
}

const ws = new WebSocket('__WSS_URL__'); 
ws.onopen = () => { console.log("WebSocket 已连接"); }; 

ws.onmessage = (e) => {
    try {
        const d = JSON.parse(e.data); 
        if (d.translation) {
            display.innerText = d.translation; 
        }
    } catch(err) {
        console.error(err);
    }
};

btn.onclick = async () => {
    if (!vapi) {
        msg.innerText = '❌ Vapi 未初始化'; 
        return;
    }

    try {
        // 修正点：v2.x SDK 中使用状态判断而非 isCallActive()
        const status = vapi.getStatus(); 
        
        if (status === 'loading' || status === 'started') {
            await vapi.stop(); [cite: 7]
            msg.innerText = '🛑 已停止'; [cite: 8]
            btn.innerText = '开始实时翻译'; [cite: 8]
            btn.style.background = '#00cc66'; [cite: 8]
        } else {
            msg.innerText = '⏳ 正在启动麦克风...';
            await vapi.start('__ASSISTANT_ID__'); [cite: 9]
            msg.innerText = '🎙️ 正在监听'; [cite: 9]
            btn.innerText = '停止翻译'; [cite: 10]
            btn.style.background = '#ff4b4b'; [cite: 10]
        }
    } catch(err) {
        console.error(err);
        msg.innerText = '❌ 启动失败，请确保已允许麦克风权限'; 
    }
};

// 监听 Vapi 内部状态变化，保持 UI 同步
vapi.on('call-end', () => {
    msg.innerText = '🛑 通话已结束';
    btn.innerText = '开始实时翻译';
    btn.style.background = '#00cc66';
});

</script>
</body>
</html>
"""

# ===== 替换变量 =====
html_code = (
    html_code
    .replace("__PUBLIC_KEY__", VAPI_PUBLIC_KEY) 
    .replace("__WSS_URL__", WSS_URL) 
    .replace("__ASSISTANT_ID__", VAPI_ASSISTANT_ID) 
)

# ===== 渲染 HTML (增加关键的麦克风权限) =====
components.html(
    html_code,
    height=420,
    scrolling=False,
    
)