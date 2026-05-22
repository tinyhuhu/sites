import streamlit as st
import datetime
import boto3

# --- 1. 页面基本配置 ---
st.set_page_config(
    page_title="Bedrock Multi-LLM Chatbot",
    page_icon="☁️",
    layout="wide"
)

st.title("☁️ AWS Bedrock 多模态对话系统")
st.caption("前端采用 Streamlit，后端通过 boto3 直接调用 AWS Bedrock 基座模型并具备强健的流式容错解析。")


# --- 2. 初始化 Session State：维护聊天记录 ---
if "messages" not in st.session_state:
    st.session_state.messages = []


# --- 3. 侧边栏：模型选择 ---
with st.sidebar:
    st.header("⚙️ AWS Bedrock 配置")

    model_mapping = {
        # 下面这些模型 ID 请根据你账号实际可用情况调整
        "Google Gemma-3": "google.gemma-3-12b-it",
        "GPT OSS Safeguard": "openai.gpt-oss-safeguard-120b",
        "Deepseek 3.2": "deepseek.v3.2",

        # Claude via US geo inference profile
        "Claude Haiku 4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "Claude Sonnet 4.6": "us.anthropic.claude-sonnet-4-6",

        # 当前你的 AWS Account 还没有 Opus 4.7 权限，保留但会在报错时友好提示
        #"Claude Opus 4.7（需 AWS 账号开通）": "us.anthropic.claude-opus-4-7",
    }

    selected_model_label = st.selectbox(
        "选择 Bedrock 模型",
        list(model_mapping.keys())
    )

    bedrock_model_id = model_mapping[selected_model_label]

    st.divider()

    if st.button("🗑️ 清空历史对话", use_container_width=True):
        st.session_state.messages = []
        st.rerun()


# --- 4. 渲染历史聊天记录 ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("content"):
            st.markdown(message["content"])

        if "files" in message and message["files"]:
            for file in message["files"]:
                if file["type"].startswith("image/"):
                    st.image(file["bytes"], caption=file["name"], width=300)
                else:
                    st.caption(f"📄 已上传文档: {file['name']}")


# --- 5. 处理用户输入：文字 + 图片/文档 ---
prompt_input = st.chat_input(
    placeholder="向 Bedrock 发送消息，或在此上传图片/文档...",
    accept_file="multiple",
    file_type=["png", "jpg", "jpeg", "pdf", "txt"]
)


if prompt_input:
    user_text = prompt_input.text or ""
    uploaded_files_data = []

    if prompt_input.files:
        for f in prompt_input.files:
            uploaded_files_data.append({
                "name": f.name,
                "type": f.type or "",
                "bytes": f.read()
            })

    if user_text or uploaded_files_data:
        # --- 5.1 保存并渲染用户消息 ---
        current_user_msg = {
            "role": "user",
            "content": user_text,
            "files": uploaded_files_data
        }

        st.session_state.messages.append(current_user_msg)

        with st.chat_message("user"):
            if user_text:
                st.markdown(user_text)

            for file in uploaded_files_data:
                if file["type"].startswith("image/"):
                    st.image(file["bytes"], caption=file["name"], width=300)
                else:
                    st.caption(f"📄 已上传文档: {file['name']}")

        # --- 6. 调用 Bedrock ConverseStream API ---
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            status_placeholder = st.empty()
            model_id_placeholder = st.empty()

            full_response = ""

            # 这里使用 placeholder，后面可以动态更新文字
            status_placeholder.caption(f"正在通过 Bedrock ({selected_model_label}) 生成回复...")
            model_id_placeholder.caption(f"当前实际调用的 modelId: `{bedrock_model_id}`")

            try:
                # 初始化 Bedrock Runtime 客户端
                bedrock_client = boto3.client(
                    service_name="bedrock-runtime",
                    region_name="us-east-2",
                    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
                )

                # 构造 Bedrock Converse API 所需的 content blocks
                bedrock_contents = []

                # --- 6.1 添加上传的图片 / PDF / TXT 文件 ---
                for file in uploaded_files_data:
                    file_name = file["name"]
                    file_type = file["type"]
                    file_bytes = file["bytes"]
                    file_name_lower = file_name.lower()

                    # 处理图片
                    if file_type.startswith("image/"):
                        img_format = file_type.split("/")[-1].lower()

                        if img_format == "jpg":
                            img_format = "jpeg"

                        bedrock_contents.append({
                            "image": {
                                "format": img_format,
                                "source": {
                                    "bytes": file_bytes
                                }
                            }
                        })

                    # 处理 PDF
                    elif file_type == "application/pdf" or file_name_lower.endswith(".pdf"):
                        # Bedrock document name 建议只使用简单字符
                        safe_doc_name = (
                            file_name.rsplit(".", 1)[0]
                            .replace(" ", "_")
                            .replace("-", "_")
                        )[:20]

                        bedrock_contents.append({
                            "document": {
                                "format": "pdf",
                                "name": safe_doc_name,
                                "source": {
                                    "bytes": file_bytes
                                }
                            }
                        })

                    # 处理 TXT：把文本内容直接塞进 text block
                    elif file_type == "text/plain" or file_name_lower.endswith(".txt"):
                        text_content = file_bytes.decode("utf-8", errors="replace")

                        bedrock_contents.append({
                            "text": (
                                f"以下是用户上传的文本文件《{file_name}》的内容：\n\n"
                                f"{text_content}"
                            )
                        })

                    # 其他暂不支持的文件类型
                    else:
                        bedrock_contents.append({
                            "text": (
                                f"用户上传了文件《{file_name}》，"
                                f"但当前系统暂不支持解析该文件类型：{file_type}"
                            )
                        })

                # --- 6.2 添加用户文本 Prompt ---
                if user_text:
                    bedrock_contents.append({
                        "text": user_text
                    })

                # 如果用户只上传了空文件或没有有效内容
                if not bedrock_contents:
                    bedrock_contents.append({
                        "text": "用户没有提供有效的文本或文件内容。"
                    })

                messages_payload = [
                    {
                        "role": "user",
                        "content": bedrock_contents
                    }
                ]

                # --- 6.3 动态注入当前系统时间 ---
                now = datetime.datetime.now()
                weekdays = [
                    "星期一",
                    "星期二",
                    "星期三",
                    "星期四",
                    "星期五",
                    "星期六",
                    "星期日"
                ]

                current_time_string = (
                    f"当前准确的系统时间是："
                    f"{now.strftime('%Y年%m月%d日')}，"
                    f"{weekdays[now.weekday()]}。"
                )

                system_prompts = [
                    {
                        "text": (
                            "你是一个部署在企业生产环境中的 AI 助手。"
                            "请务必基于以下给出的时间事实，"
                            "来准确回答用户关于今天、明天、日期或星期几的询问。"
                            f"{current_time_string}"
                        )
                    }
                ]

                # --- 6.4 调用 Bedrock 流式对话 API ---
                response = bedrock_client.converse_stream(
                    modelId=bedrock_model_id,
                    messages=messages_payload,
                    system=system_prompts
                )

                # --- 6.5 强健的流式解析 ---
                for chunk in response.get("stream", []):
                    # 标准 ConverseStream 返回结构
                    if "contentBlockDelta" in chunk:
                        delta = chunk["contentBlockDelta"].get("delta", {})
                        text_chunk = delta.get("text", "")

                        if text_chunk:
                            full_response += text_chunk
                            response_placeholder.markdown(full_response + "▌")

                    # 兼容某些自定义中转网关返回 chunk bytes 的结构
                    elif "chunk" in chunk:
                        try:
                            bytes_data = chunk["chunk"].get("bytes", b"")
                            text_chunk = bytes_data.decode("utf-8")

                            if text_chunk:
                                full_response += text_chunk
                                response_placeholder.markdown(full_response + "▌")
                        except Exception:
                            pass

                # 最终渲染完整回复，去掉光标
                response_placeholder.markdown(full_response)

                # 生成完成后，更新状态文字
                status_placeholder.caption(f"✅ Bedrock ({selected_model_label}) 回复完成")

                # 如果你不想最终用户看到 modelId，可以取消下一行注释
                # model_id_placeholder.empty()

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })

            except Exception as e:
                error_text = str(e)

                # 出错时，也更新状态文字
                status_placeholder.caption(f"❌ Bedrock ({selected_model_label}) 回复失败")

                if (
                    "not available for this account" in error_text
                    and "claude-opus-4-7" in error_text
                ):
                    st.error(
                        "Claude Opus 4.7 当前未对这个 AWS Account 开放。"
                        "Haiku/Sonnet 可用说明代码链路正常；"
                        "请从 Bedrock Playground 测试 Opus 4.7，"
                        "或联系 AWS Support/Sales 开通账号级访问。"
                    )
                else:
                    st.error(f"调用 AWS Bedrock 时发生错误: {error_text}")