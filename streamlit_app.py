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
        enableTrace=True  # 开启 Trace 以获取更详细的上下文
    )
    
    full_answer = ""
    all_citations = []

    for event in response.get("completion"):
        # 获取文本内容
        if "chunk" in event:
            chunk = event["chunk"]
            full_answer += chunk.get("bytes").decode()
            
            # 关键：提取引用信息
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
    # ... (1 & 2 部分：渲染历史记录保持一致，注意也需开启 unsafe_allow_html=True)
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"], unsafe_allow_html=True)
            # ... (历史引用 expander 逻辑)

    # 3. 处理输入
    if prompt := st.chat_input("请问关于这些文档的问题..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 4. 获取 AI 回复
        with st.chat_message("assistant"):
            with st.spinner("Claude 4.5 正在精准标注关键条款..."):
                try:
                    ctx = get_script_run_ctx()
                    session_id = ctx.session_id if ctx else "default_session"
                    
                    result = ask_bedrock_agent(prompt, session_id)
                    answer = result["answer"]
                    citations = result["citations"]

                    # --- 改进的高亮+加粗处理逻辑 ---
                    display_text = ""
                    last_end = 0
                    
                    # 按照引用在回答文本中的起始位置排序 [cite: 115]
                    sorted_citations = sorted(
                        citations, 
                        key=lambda x: x.get("generatedResponsePart", {}).get("textResponsePart", {}).get("span", {}).get("start", 0)
                    )

                    for cit in sorted_citations:
                        part = cit.get("generatedResponsePart", {}).get("textResponsePart", {})
                        span = part.get("span", {})
                        start, end = span.get("start", 0), span.get("end", 0)
                        
                        # 拼接：普通文本 + (加粗 + 高亮) 引用内容
                        display_text += answer[last_end:start]
                        cited_text = answer[start:end]
                        
                        # 使用 HTML 结合加粗和背景色
                        highlight_style = (
                            "background-color: #FFEB3B; " # 明黄色背景
                            "color: black; "             # 黑色文字确保对比度
                            "font-weight: bold; "       # 【关键】加粗字体
                            "padding: 0 2px; "
                            "border-radius: 2px;"
                        )
                        display_text += f"<mark style='{highlight_style}'>{cited_text}</mark>"
                        last_end = end
                    
                    display_text += answer[last_end:] # 拼接剩余部分
                    # --- 逻辑结束 ---

                    # 渲染最终效果
                    st.write(display_text, unsafe_allow_html=True)

                    # 底部原文参考（保持原样）
                    if citations:
                        st.markdown("---")
                        for idx, cit in enumerate(citations):
                            ref = cit["retrievedReferences"][0]
                            uri = ref["location"]["s3Location"]["uri"]
                            text = ref["content"]["text"]
                            with st.expander(f"依据 [{idx+1}]: {uri.split('/')[-1]}"):
                                st.write(f"**原始文本：**\n{text}")

                    # 存入 session_state
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": display_text, 
                        "citations": citations
                    })
                    
                except Exception as e:
                    st.error(f"分析出错: {str(e)}")

with tab2:
    st.subheader("关键风险点分析")
    st.warning("⚠️ 发现 2 处潜在合同违约风险，建议核查交付日期。")
    st.write("---")
    st.text_area("AI 自动生成的摘要", "本文档为 XX 公司与 YY 公司的采购合同，总金额 500 万...")

with tab3:
    st.info("此处可集成 PDF 预览组件，显示原始扫描件内容。")
