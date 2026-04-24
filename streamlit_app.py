import streamlit as st
import time

import boto3
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

def get_bedrock_runtime():
    # 自动从 st.secrets 读取 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY
    session = boto3.Session(
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets["AWS_DEFAULT_REGION"]
    )
    return session.client("bedrock-agent-runtime")


def ask_bedrock_agent(input_text, session_id):
    client = get_bedrock_runtime()
    
    response = client.invoke_agent(
        agentId=st.secrets["BEDROCK_AGENT_ID"],
        agentAliasId=st.secrets["BEDROCK_AGENT_ALIAS_ID"],
        sessionId=session_id,
        inputText=input_text,
        enableTrace=True 
    )
    
    full_answer = ""
    all_citations = []

    for event in response.get("completion"):
        # 1. 安全检查：确保 event 是字典且包含 chunk
        chunk = event.get("chunk")
        if chunk and "bytes" in chunk:
            # 解码文本内容
            text_part = chunk["bytes"].decode()
            full_answer += text_part
            
            # 2. 提取引用信息 (Citations)
            if "attribution" in chunk:
                citations = chunk["attribution"].get("citations", [])
                all_citations.extend(citations)
                
    return {"answer": full_answer, "citations": all_citations}


def upload_to_s3(file_obj, bucket_name, s3_key):
    """将 Streamlit 上传的文件流上传到 S3"""
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets["AWS_DEFAULT_REGION"]
    )
    try:
        s3_client.upload_fileobj(file_obj, bucket_name, s3_key)
        return True
    except Exception as e:
        st.error(f"S3 上传失败: {e}")
        return False

def start_ingestion_job():
    """触发 Bedrock 知识库同步任务"""
    # 注意：同步任务使用 bedrock-agent 客户端
    client = boto3.client(
        "bedrock-agent", 
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets["AWS_DEFAULT_REGION"]
    )
    try:
        client.start_ingestion_job(
            knowledgeBaseId=st.secrets["BEDROCK_KNOWLEDGE_BASE_ID"],
            dataSourceId=st.secrets["BEDROCK_DATA_SOURCE_ID"]
        )
        return True
    except Exception as e:
        st.error(f"同步任务启动失败: {e}")
        return False



# 1. 页面基本配置
st.set_page_config(page_title="2律所 AI 知识助手", layout="wide")

# 2. 侧边栏设计
with st.sidebar:
    st.title("📂 卷宗管理")
    st.info("支持扫描件 OCR 及长文档分析")
    
    # 案件分类
    case_type = st.selectbox("选择法律领域", ["民事合同", "刑事诉讼", "企业合规", "知识产权"])
    
    # 文件上传
    uploaded_files = st.file_uploader("上传法律文档 (PDF)", type=['pdf'], accept_multiple_files=True)
    
    if uploaded_files:
        st.success(f"已选中 {len(uploaded_files)} 个文档")
        
        # 直接使用新的逻辑按钮，替换掉原来的 if st.button("开始分析/同步至 AWS"):
        if st.button("🚀 开始同步至法律知识库"):
            with st.status("正在处理文档...", expanded=True) as status:
                all_success = True
                
                # 1. 逐个上传到 S3
                for uploaded_file in uploaded_files:
                    st.write(f"正在上传: {uploaded_file.name}...")
                    success = upload_to_s3(
                        uploaded_file, 
                        st.secrets["AWS_S3_BUCKET_NAME"], 
                        f"legal_docs/{uploaded_file.name}"
                    )
                    if not success:
                        all_success = False

                # 2. 触发 Bedrock 同步
                if all_success:
                    st.write("已完成 S3 上传，正在触发 Bedrock 向量化索引...")
                    if start_ingestion_job():
                        status.update(label="✅ 同步任务已启动！AI 正在学习新文档...", state="complete")
                        st.toast("知识库正在后台更新，通常需要 1-2 分钟。")
                    else:
                        status.update(label="❌ 触发同步失败", state="error")


# 3. 主界面设计
st.title("⚖️ 法律文书智能助手")

# 创建标签页：对话分析、文档摘要、原始查看
tab1, tab2, tab3 = st.tabs(["💬 智能对话", "📝 自动摘要", "🔍 原文预览"])

with tab1:
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # 渲染历史记录（使用 write 配合 HTML）
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message.get("content", ""), unsafe_allow_html=True)
            if "citations" in message and message["citations"]:
                with st.expander("查看历史引用依据"):
                    for idx, cit in enumerate(message["citations"]):
                        ref = cit["retrievedReferences"][0]
                        file_name = ref["location"]["s3Location"]["uri"].split("/")[-1]
                        st.info(f"[{idx+1}] {file_name}: {ref['content']['text']}")

    if prompt := st.chat_input("请问关于这些文档的问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Claude 4.5 正在精准分析关键数据..."):
                try:
                    ctx = get_script_run_ctx()
                    session_id = ctx.session_id if ctx else "default_session"
                    
                    result = ask_bedrock_agent(prompt, session_id)
                    answer = result["answer"]
                    citations = result["citations"]

                    # --- 精准高亮 + 加粗 + 自动引号处理 ---
                    display_text = ""
                    last_end = 0

                    # 按照文本位置排序防止错位 [cite: 17]
                    # 按照文本位置排序防止错位
                    sorted_citations = sorted(citations, key=lambda x: x.get("generatedResponsePart", {}).get("textResponsePart", {}).get("span", {}).get("start", 0))

                    for cit in sorted_citations:
                        span = cit.get("generatedResponsePart", {}).get("textResponsePart", {}).get("span", {}) 
                        start, end = span.get("start", 0), span.get("end", 0)
                        
                        # 1. 拼接引用前的普通文本
                        display_text += answer[last_end:start]
                        
                        # 2. 提取 AI 标注的引用片段
                        raw_cited_text = answer[start:end].strip()
                        
                        # --- 核心词提取逻辑 ---
                        # 我们把片段拆开，只给最像“字段名”的部分加粗
                        words = raw_cited_text.split()
                        processed_words = []
                        for word in words:
                            # 清理掉单词两边的标点符号
                            clean_word = word.strip('.,;:"“”\'')
                            # 识别逻辑：如果单词包含下划线，或者看起来像代码字段（不含空格且长度适中）
                            if "_" in clean_word or (len(clean_word) > 2 and clean_word.islower()):
                                processed_words.append(f"<b>\"{clean_word}\"</b>")
                            else:
                                processed_words.append(word)
                        
                        display_text += " ".join(processed_words)
                        last_end = end

                    display_text += answer[last_end:]

                    # 渲染最终结果
                    st.write(display_text, unsafe_allow_html=True)

                    if citations:
                        st.markdown("---")
                        for idx, cit in enumerate(citations):
                            ref = cit["retrievedReferences"][0]
                            st.caption(f"📍 引用 [{idx+1}]: {ref['location']['s3Location']['uri'].split('/')[-1]}")

                    st.session_state.messages.append({"role": "assistant", "content": display_text, "citations": citations})
                except Exception as e:
                    st.error(f"处理失败: {str(e)}")

with tab2:
    st.subheader("关键风险点分析")
    st.warning("⚠️ 发现 2 处潜在合同违约风险，建议核查交付日期。")
    st.write("---")
    st.text_area("AI 自动生成的摘要", "本文档为 XX 公司与 YY 公司的采购合同，总金额 500 万...")

with tab3:
    st.info("此处可集成 PDF 预览组件，显示原始扫描件内容。")
