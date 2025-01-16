import streamlit as st
from zhipuai import ZhipuAI
import os
from dotenv import load_dotenv
import PyPDF2
import docx
import io
from typing import Optional, Dict, List
import json

# 加载环境变量
load_dotenv()
client = ZhipuAI(api_key=os.getenv("ZHIPUAI_API_KEY"))

def extract_text_from_pdf(pdf_file) -> str:
    """从PDF文件中提取文本"""
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        st.error(f"PDF文件读取失败: {str(e)}")
        return ""

def extract_text_from_docx(docx_file) -> str:
    """从Word文件中提取文本"""
    try:
        doc = docx.Document(docx_file)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        st.error(f"Word文件读取失败: {str(e)}")
        return ""

def analyze_resume(text: str, position: Optional[str] = None) -> str:
    """使用智谱AI分析简历内容"""
    system_prompt = """
    #Role: Resume Analyst : 专注于从简历中提取关键信息，并将其转化为结构化数据。
    ## Goals
    提取简历中的技能、工作经历、教育背景和项目经历。
    将提取的信息转化为结构化数据格式。
    ## Constrains
    必须保持原始简历内容的准确性和完整性。
    结构化数据应清晰、易于理解和检索。
    ## Skills
    简历内容分析能力
    数据结构化处理能力
    精确的信息提取和总结能力
    ## Outputformat
    //结构化数据格式，包括明确的字段和相应的信息。
    ## Workflow
    1.仔细阅读并分析简历内容："简历内容"。
    2.提取关键信息，包括技能、工作经历、教育背景和项目经历。
    3.将提取的信息按照预定的结构化数据格式进行组织。
    4.输出结构化数据。
    """
    
    user_prompt = f"""请分析以下简历内容，生成候选人画像：
    
    目标岗位：{position if position else '未指定'}
    
    简历内容：
    {text}
    """
    
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            top_p=0.8,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"简历分析失败: {str(e)}")
        return ""

def analyze_job_description(description: str) -> str:
    """分析工作岗位要求"""
    system_prompt = """
    # Role: Job Description Analyst : 分析并提取岗位描述中的关键要求，转换为结构化格式
    ## Goals: 从给定的岗位描述中提取关键要求，包括技能要求、项目经验、最低学历、相关证书和资格认证、语言能力等。
    ## Constrains: 必须遵循结构化格式，确保信息准确无误。
    ## Skills:
    精准的信息提取能力
    对岗位描述的深入理解
    快速准确的数据整理能力
    ## Output Format:
    技能要求: 列表格式
    项目经验: 具体描述或年限要求
    最低学历: 学历名称
    相关证书和资格认证: 列表格式
    语言能力: 语言名称及水平要求
    ## Workflow:
    读取并分析岗位描述文本：文本内容"。
    提取关键要求，分类整理。
    按照指定的结构化格式输出结果。
    """
    
    user_prompt = f"请分析以下工作岗位描述，并提取关键要求：\n\n{description}"
    
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            top_p=0.8,
            max_tokens=2500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"岗位分析失败: {str(e)}")
        return ""

def calculate_similarity(job_analysis: str, resume_analysis: str) -> str:
    """计算岗位要求和候选人画像的匹配度"""
    system_prompt = """
    # Goal 请基于以下岗位和候选人画像，计算语义相似度，输出候选人与岗位的匹配度评分（0-100%）。
    """
    
    user_prompt = f"""
    岗位画像：
    {job_analysis}
    
    候选人画像：
    {resume_analysis}
    """
    
    try:
        response = client.chat.completions.create(
            model="glm-4-flash",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            top_p=0.8,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"匹配度计算失败: {str(e)}")
        return ""

def main():
    st.title("📄 AI智能招聘助手")
    
    tab1, tab2, tab3 = st.tabs(["简历分析", "岗位分析", "匹配度计算"])
    
    with tab1:
        st.header("简历分析")
        uploaded_file = st.file_uploader("上传简历文件", type=['pdf', 'docx'])
        position = st.text_input("目标岗位（可选）", placeholder="例如：Python开发工程师")
        
        if uploaded_file is not None:
            file_extension = uploaded_file.name.split('.')[-1].lower()
            resume_text = ""
            
            with st.spinner("正在读取文件..."):
                if file_extension == 'pdf':
                    resume_text = extract_text_from_pdf(uploaded_file)
                elif file_extension == 'docx':
                    resume_text = extract_text_from_docx(uploaded_file)
            
            if resume_text:
                st.success("文件读取成功！")
                
                with st.expander("查看提取的文本内容", expanded=False):
                    st.text(resume_text)
                
                if st.button("开始分析", key="analyze_resume"):
                    with st.spinner("AI正在分析简历..."):
                        analysis = analyze_resume(resume_text, position)
                        if analysis:
                            st.session_state['resume_analysis'] = analysis
                            st.markdown(analysis)
            else:
                st.error("文件内容提取失败，请检查文件格式是否正确。")
    
    with tab2:
        st.header("岗位要求分析")
        job_description = st.text_area(
            "请输入岗位描述",
            height=200,
            placeholder="请粘贴完整的职位描述..."
        )
        
        if st.button("分析岗位要求", key="analyze_job"):
            if job_description:
                with st.spinner("正在分析岗位要求..."):
                    job_analysis = analyze_job_description(job_description)
                    if job_analysis:
                        st.markdown(job_analysis)
                        st.session_state['job_analysis'] = job_analysis
            else:
                st.warning("请输入岗位描述")
    
    with tab3:
        st.header("匹配度计算")
        if 'job_analysis' not in st.session_state:
            st.warning("请先在岗位分析标签页中分析岗位要求")
            return
            
        if 'resume_analysis' not in st.session_state:
            st.warning("请先在简历分析标签页中分析候选人简历")
            return
            
        if st.button("计算匹配度", key="calculate_match"):
            with st.spinner("正在计算匹配度..."):
                match_result = calculate_similarity(
                    st.session_state['job_analysis'],
                    st.session_state['resume_analysis']
                )
                if match_result:
                    st.markdown(match_result)

if __name__ == "__main__":
    main()
