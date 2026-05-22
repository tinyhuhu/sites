import streamlit as st
import datetime
import boto3


# =========================
# 0. 可调整参数
# =========================

AWS_REGION = "us-east-2"

# 传给模型的历史消息数量。数值越大，memory 越强，但 token 成本越高
MAX_HISTORY_MESSAGES = 12

# TXT 文件最多保存多少字符进 memory，避免超长文件导致上下文爆炸
MAX_TEXT_FILE_CHARS_FOR_MEMORY = 20000


# =========================
# 1. 页面基本配置
# =========================

st.set_page_config(
    page_title="Bedrock Multi-LLM Chatbot",
    page_icon="☁️",
    layout="wide"
)

st.title("☁️ AWS Bedrock 多模态对话系统")
st.caption("前端采用 Streamlit，后端通过 boto3 直接调用 AWS Bedrock 基座模型并具备强健的流式容错解析。")


# =========================
# 2. 初始化 Session State
# =========================

if "messages" not in st.session_state:
    st.session_state.messages = []


# =========================
# 3. 工具函数
# =========================

def make_safe_doc_name(file_name: str) -> str:
    """
    Bedrock document.name 建议只使用简单字符。
    """
    base_name = file_name.rsplit(".", 1)[0]
    safe_name = (
        base_name
        .replace(" ", "_")
        .replace("-", "_")
        .replace(".", "_")
        .replace("(", "_")
        .replace(")", "_")
    )
    return safe_name[:20] or "uploaded_document"


def build_bedrock_messages_from_history(current_user_content):
    """
    把 Streamlit session_state 中的历史消息转换成 Bedrock Converse API messages 格式。
    current_user_content 是当前这一轮用户输入，已经包含文字/图片/PDF/TXT 等 content blocks。

    注意：
    - 历史消息只传文本，不重复传图片/PDF bytes，避免 token/cost 爆炸。
    - TXT 文件内容会被保存成 model_memory_text，后续追问时模型还能看到。
    """

    bedrock_messages = []

    recent_messages = st.session_state.messages[-MAX_HISTORY_MESSAGES:]

    for msg in recent_messages:
        role = msg.get("role")
        content = msg.get("content", "")
        model_memory_text = msg.get("model_memory_text", "")

        # 优先使用专门给模型看的 memory text
        text_for_model = model_memory_text or content

        if not text_for_model:
            continue

        if role == "user":
            bedrock_messages.append({
                "role": "user",
                "content": [
                    {
                        "text": text_for_model
                    }
                ]
            })

        elif role == "assistant":
            bedrock_messages.append({
                "role": "assistant",
                "content": [
                    {
                        "text": text_for_model
                    }
                ]
            })

    # 加入当前这一轮用户消息
    bedrock_messages.append({
        "role": "user",
        "content": current_user_content
    })

    return bedrock_messages


def build_current_user_content_and_memory(user_text, uploaded_files_data):
    """
    构造当前这一轮要发给 Bedrock 的 content blocks，
    同时构造一份用于后续 memory 的纯文本描述。
    """

    bedrock_contents = []
    memory_parts = []

    # 先记录用户当前输入
    if user_text:
        memory_parts.append(f"用户说：{user_text}")

    # 处理上传文件
    for file in uploaded_files_data:
        file_name = file["name"]
        file_type = file["type"]
        file_bytes = file["bytes"]
        file_name_lower = file_name.lower()

        # 图片
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

            memory_parts.append(
                f"用户上传了一张图片：{file_name}。"
                f"后续如需基于图片继续追问，最好参考助手上一轮对图片的分析。"
            )

        # PDF
        elif file_type == "application/pdf" or file_name_lower.endswith(".pdf"):
            safe_doc_name = make_safe_doc_name(file_name)

            bedrock_contents.append({
                "document": {
                    "format": "pdf",
                    "name": safe_doc_name,
                    "source": {
                        "bytes": file_bytes
                    }
                }
            })

            memory_parts.append(
                f"用户上传了一个 PDF 文件：{file_name}。"
                f"PDF 原文没有在历史中重复保存，后续追问时应结合助手上一轮对该 PDF 的总结。"
            )

        # TXT
        elif file_type == "text/plain" or file_name_lower.endswith(".txt"):
            text_content = file_bytes.decode("utf-8", errors="replace")

            bedrock_contents.append({
                "text": (
                    f"以下是用户上传的文本文件《{file_name}》的内容：\n\n"
                    f"{text_content}"
                )
            })

            # TXT 文件内容也保存进 memory，方便后续追问
            memory_text_content = text_content[:MAX_TEXT_FILE_CHARS_FOR_MEMORY]

            if len(text_content) > MAX_TEXT_FILE_CHARS_FOR_MEMORY:
                memory_text_content += "\n\n[注意：该 TXT 文件内容过长，memory 中只保留了前一部分。]"

            memory_parts.append(
                f"用户上传了文本文件《{file_name}》，内容如下：\n\n"
                f"{memory_text_content}"
            )

        # 其他暂不支持的文件类型
        else:
            bedrock_contents.append({
                "text": (
                    f"用户上传了文件《{file_name}》，"
                    f"但当前系统暂不支持解析该文件类型：{file_type}"
                )
            })

            memory_parts.append(
                f"用户上传了文件《{file_name}》，但当前系统暂不支持解析该文件类型：{file_type}。"
            )

    # 最后加入用户文字 prompt
    if user_text:
        bedrock_contents.append({
            "text": user_text
        })

    if not bedrock_contents:
        bedrock_contents.append({
            "text": "用户没有提供有效的文本或文件内容。"
        })

    model_memory_text = "\n\n".join(memory_parts).strip()

    return bedrock_contents, model_memory_text


# =========================
# 4. 侧边栏：模型选择
# =========================

with st.sidebar:
    st.header("⚙️ AWS Bedrock 配置")

    model_mapping = {
        "Google Gemma-3": "google.gemma-3-12b-it",
        "GPT OSS Safeguard": "openai.gpt-oss-safeguard-120b",
        "Deepseek 3.2": "deepseek.v3.2",

        # Claude via US geo inference profile
        "Claude Haiku 4.5": "us.anthropic.claude-haiku-4-5-20251001-v1:0",
        "Claude Sonnet 4.6": "us.anthropic.claude-sonnet-4-6",

        # 你的 AWS Account 当前可能还没有 Opus 4.7 权限
        "Claude Opus 4.7（需 AWS 账号开通）": "us.anthropic.claude-opus-4-7",
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


# =========================
# 5. 渲染历史聊天记录
# =========================

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


# =========================
# 6. 处理用户输入
# =========================

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
        # 先构造当前用户消息，但暂时不要 append 到 session_state
        # 否则 build history 时会把当前消息重复放进去
        current_user_msg = {
            "role": "user",
            "content": user_text,
            "files": uploaded_files_data
        }

        # 渲染当前用户消息
        with st.chat_message("user"):
            if user_text:
                st.markdown(user_text)

            for file in uploaded_files_data:
                if file["type"].startswith("image/"):
                    st.image(file["bytes"], caption=file["name"], width=300)
                else:
                    st.caption(f"📄 已上传文档: {file['name']}")

        # 调用 Bedrock
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            status_placeholder = st.empty()
            model_id_placeholder = st.empty()

            full_response = ""

            status_placeholder.caption(f"正在通过 Bedrock ({selected_model_label}) 生成回复...")
            model_id_placeholder.caption(f"当前实际调用的 modelId: `{bedrock_model_id}`")

            try:
                # 初始化 Bedrock Runtime 客户端
                bedrock_client = boto3.client(
                    service_name="bedrock-runtime",
                    region_name=AWS_REGION,
                    aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
                    aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"]
                )

                # 构造当前这一轮的 content blocks 和 memory text
                bedrock_contents, current_model_memory_text = build_current_user_content_and_memory(
                    user_text=user_text,
                    uploaded_files_data=uploaded_files_data
                )

                # 把历史消息 + 当前消息一起发给 Bedrock
                messages_payload = build_bedrock_messages_from_history(
                    current_user_content=bedrock_contents
                )

                # 动态注入当前系统时间
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
                            "你正在和用户进行连续多轮对话。"
                            "请充分利用 messages 中提供的历史上下文来回答追问。"
                            "如果用户说“这个”“它”“刚才那个”“上面的问题”，"
                            "通常是在指代前文中的内容。"
                            "请务必基于以下给出的时间事实，"
                            "来准确回答用户关于今天、明天、日期或星期几的询问。"
                            f"{current_time_string}"
                        )
                    }
                ]

                # 调用 Bedrock 流式对话 API
                response = bedrock_client.converse_stream(
                    modelId=bedrock_model_id,
                    messages=messages_payload,
                    system=system_prompts
                )

                # 流式解析
                for chunk in response.get("stream", []):
                    if "contentBlockDelta" in chunk:
                        delta = chunk["contentBlockDelta"].get("delta", {})
                        text_chunk = delta.get("text", "")

                        if text_chunk:
                            full_response += text_chunk
                            response_placeholder.markdown(full_response + "▌")

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

                # 更新状态
                status_placeholder.caption(f"✅ Bedrock ({selected_model_label}) 回复完成")

                # 不想给最终用户看到 modelId 的话，保留这一行
                # 想继续调试就注释掉这一行
                model_id_placeholder.empty()

                # 这时候再把当前用户消息写入 memory
                current_user_msg["model_memory_text"] = current_model_memory_text
                st.session_state.messages.append(current_user_msg)

                # 保存 assistant 回复进 memory
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response,
                    "model_memory_text": full_response
                })

            except Exception as e:
                error_text = str(e)

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