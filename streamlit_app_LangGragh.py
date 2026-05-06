import streamlit as st
import requests
import json
import uuid

# --- 配置区 ---
# 将此处替换为你从 AWS 控制台获取的实际 Function URL
LAMBDA_URL = "https://bw27k2swbdwbu3kqmphitxok3i0ofhoa.lambda-url.us-east-2.on.aws/"

st.set_page_config(page_title="Agentic AI Chatbot", page_icon="🤖")

# --- 状态初始化 ---
# 1. 维护一个跨刷新存在的 Session ID，用于 DynamoDB 查询历史
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# 2. 存储前端显示的聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("AI 智能助手")
st.caption(f"当前会话 ID: {st.session_state.session_id}")

# --- 渲染历史消息 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 用户输入处理 ---
if prompt := st.chat_input("请输入您的问题..."):
    # 展示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 发送请求到 Lambda
    with st.chat_message("assistant"):
        with st.spinner("思考中..."):
            try:
                # 构造 Payload，传递 session_id 和当前消息
                payload = {
                    "session_id": st.session_state.session_id,
                    "message": prompt
                }

                # 发送 POST 请求
                response = requests.post(
                    LAMBDA_URL,
                    json=payload,
                    timeout=60  # LLM 生成可能较慢，建议设置较长的超时
                )

                if response.status_code == 200:
                    # 解析 Lambda 返回的 JSON
                    # 注意：如果 Lambda 返回的是直接 JSON，则 response.json() 即可
                    res_data = response.json()
                    
                    # 假设你的 Lambda 返回格式为 {"answer": "..."}
                    full_response = res_data.get("answer", "未收到有效回复")
                    
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    st.error(f"调用失败 (HTTP {response.status_code}): {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"请求发生异常: {e}")

# --- 侧边栏辅助功能 ---
with st.sidebar:
    if st.button("开启新对话"):
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()