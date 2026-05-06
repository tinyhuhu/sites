import streamlit as st
import boto3
import json
import uuid

# 为当前用户会话生成唯一 ID
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("Serverless 多轮对话")

if "messages" not in st.session_state:
    st.session_state.messages = []

# 显示 UI 上的聊天记录
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    # 关键点：只发送当前消息和 session_id
    payload = {
        "session_id": st.session_state.session_id,
        "message": prompt
    }

    with st.chat_message("assistant"):
        response = boto3.client('lambda').invoke(
            FunctionName='YourLambdaName',
            Payload=json.dumps(payload)
        )
        res_data = json.loads(response['Payload'].read())
        answer = res_data['answer']
        
        st.write(answer)
        st.session_state.messages.append({"role": "assistant", "content": answer})
