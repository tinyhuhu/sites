import streamlit as st
import requests
import json
import uuid

# --- 1. 配置区 ---
# 请在你的 .streamlit/secrets.toml 中配置以下信息，或者直接在此处替换
# 建议将 URL 放入 secrets 中以增强安全性
LAMBDA_URL = st.secrets.get("LAMBDA_URL", "https://bw27k2swbdwbu3kqmphitxok3i0ofhoa.lambda-url.us-east-2.on.aws/")

st.set_page_config(page_title="LangGraph Agent 助手", page_icon="🤖")

# --- 2. 状态初始化 ---
# 维护一个跨刷新存在的 Session ID，用于触发 Lambda 端的 DynamoDB 持久化逻辑
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

# 存储前端显示的聊天记录
if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("LangGraph 智能对话终端")
st.caption(f"当前会话 ID (DynamoDB Key): {st.session_state.session_id}")

# --- 3. 渲染历史消息 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# --- 4. 用户输入与后端交互 ---
if prompt := st.chat_input("请输入指令..."):
    # 在前端展示用户消息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 准备发送给 Lambda 的 Payload
    # 既然你已经实现了 DynamoDB 逻辑，Lambda 只需要 ID 和当前消息
    payload = {
        "session_id": st.session_state.session_id,
        "message": prompt
    }

    with st.chat_message("assistant"):
        with st.spinner("Agent 正在思考并检索状态..."):
            try:
                # 使用 POST 方式调用 Lambda Function URL
                # 这种方式不需要 boto3，也就不会报 NoRegionError
                response = requests.post(
                    LAMBDA_URL,
                    json=payload,
                    timeout=90  # 考虑到 LangGraph 可能有多个节点流转，超时设置稍长
                )

                if response.status_code == 200:
                    res_data = response.json()
                    
                    # 假设你的 Lambda 返回格式为 {"answer": "..."}
                    # 如果你的 Lambda 返回的是 body 字符串，请根据实际情况解析
                    full_response = res_data.get("answer", "后端未返回有效 answer 字段")
                    
                    st.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    st.error(f"Lambda 响应异常 (HTTP {response.status_code}): {response.text}")

            except requests.exceptions.RequestException as e:
                st.error(f"连接 Lambda 失败: {e}")

# --- 5. 辅助功能 ---
with st.sidebar:
    st.header("控制台")
    if st.button("清空本地缓存并开启新会话"):
        # 重新生成 ID 后，下一次请求 Lambda 会因为找不到旧 ID 而创建新的 DynamoDB 记录
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()