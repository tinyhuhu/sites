import streamlit as st
import json
# 请确保安装了 boto3：pip install boto3
import boto3

# --- 1. 页面基本配置 ---
st.set_page_config(page_title="Bedrock Multi-LLM Chatbot", page_icon="☁️", layout="wide")
st.title("☁️ AWS Bedrock 多模态对话系统")
st.caption("前端采用 Streamlit，后端通过 boto3 直接调用 AWS Bedrock 基座模型。")

# --- 2. 初始化 Session State (维护聊天记录) ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 3. 侧边栏：AWS 凭证与模型选择 ---
with st.sidebar:
    st.header("⚙️ AWS Bedrock 配置")
    
    # 模拟你需要的模型列表（映射到 Bedrock 的 Model ID）
    model_mapping = { 
        "Google Gemma-3": "google.gemma-3-12b-it",
        "GPT OSS Safeguard": "openai.gpt-oss-safeguard-120b",
        "Deepseek 3.2": "deepseek.v3.2",
        "Claude Haiku 4.5": "anthropic.claude-haiku-4-5-20251001-v1:0",
        "Claude Sonnet 4.6": "anthropic.claude-sonnet-4-6",
        "Claude Opus 4.7": "anthropic.claude-opus-4-7"
    }
    
    selected_model_label = st.selectbox("选择 Bedrock 模型", list(model_mapping.keys()))
    bedrock_model_id = model_mapping[selected_model_label]
    
    st.divider()
    #st.subheader("🔒 AWS 认证凭证")
    #aws_access_key = st.text_input("AWS Access Key ID", type="password")
    #aws_secret_key = st.text_input("AWS Secret Access Key", type="password")
    
    
    if st.button("🗑️ 清空历史对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# --- 4. 渲染历史聊天记录 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["content"]:
            st.markdown(message["content"])
        if "files" in message and message["files"]:
            for file in message["files"]:
                if file["type"].startswith("image/"):
                    st.image(file["bytes"], caption=file["name"], width=300)
                else:
                    st.caption(f"📄 已上传文档: {file['name']}")

# --- 5. 处理用户输入 (文字 + 图片/文档) ---
prompt_input = st.chat_input(
    placeholder="向 Bedrock 发送消息，或在此上传图片/文档...",
    accept_file="multiple",
    file_type=["png", "jpg", "jpeg", "pdf", "txt"]
)

if prompt_input:
    user_text = prompt_input.text
    uploaded_files_data = []
    
    if prompt_input.files:
        for f in prompt_input.files:
            uploaded_files_data.append({
                "name": f.name,
                "type": f.type,
                "bytes": f.read()
            })

    if user_text or uploaded_files_data:
        # 渲染用户端
        current_user_msg = {"role": "user", "content": user_text, "files": uploaded_files_data}
        st.session_state.messages.append(current_user_msg)
        
        with st.chat_message("user"):
            if user_text:
                st.markdown(user_text)
            for file in uploaded_files_data:
                if file["type"].startswith("image/"):
                    st.image(file["bytes"], caption=file["name"], width=300)
                else:
                    st.caption(f"📄 已上传文档: {file['name']}")
        
        # --- 6. 后端模型调用 (Bedrock Converse API) ---
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = ""
            st.caption(f"正在通过 Bedrock ({selected_model_label}) 生成回复...")
            
            try:
                # 初始化 Bedrock 客户端
                bedrock_client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name='us-east-2',
                    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
                    #aws_region = st.text_input("AWS Region", value="us-east-1")
                )
                
                # 构造 Bedrock Converse API 所需的 messages 格式
                bedrock_contents = []
                
                # 1. 添加上传的文件/图片
                for file in uploaded_files_data:
                    if file["type"].startswith("image/"):
                        # 提取纯格式名，例如 'jpeg' 或 'png'
                        img_format = file["type"].split("/")[-1]
                        if img_format == "jpg": img_format = "jpeg"
                        bedrock_contents.append({
                            "image": {
                                "format": img_format,
                                "source": {"bytes": file["bytes"]}
                            }
                        })
                    elif file["type"] == "application/pdf":
                        bedrock_contents.append({
                            "document": {
                                "format": "pdf",
                                "name": file["name"].split(".")[0][:20], # 限制名字长度
                                "source": {"bytes": file["bytes"]}
                            }
                        })
                
                # 2. 添加文本 Prompt (文本块必须跟在多模态块后面或一同组织)
                if user_text:
                    bedrock_contents.append({"text": user_text})
                
                # 封装单次请求消息
                messages_payload = [{"role": "user", "content": bedrock_contents}]
                
                # 调用 Bedrock 流式对话 API
                response = bedrock_client.converse_stream(
                    modelId=bedrock_model_id,
                    messages=messages_payload
                )
                
                # 解析流式数据块
                for chunk in response.get('stream'):
                    if 'contentBlockDelta' in chunk:
                        text_chunk = chunk['contentBlockDelta']['delta']['text']
                        full_response += text_chunk
                        response_placeholder.markdown(full_response + "▌")
                        
                response_placeholder.markdown(full_response)
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"调用 AWS Bedrock 时发生错误: {str(e)}")
