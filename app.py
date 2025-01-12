import streamlit as st
from zhipuai import ZhipuAI
import pandas as pd
from typing import Optional, List, Dict

# 配置ZhipuAI API
client = ZhipuAI(api_key="")

def get_ai_analysis(headers: Optional[List[str]] = None, business_desc: Optional[str] = "") -> str:
    """
    获取AI分析建议
    """
    # 构建系统提示词
    system_prompt = """你是一个专业的数据分析专家，请基于用户提供的信息给出详细的分析建议。
    分析建议应该包含以下方面：
    1. 建议的数据分析维度
    2. 建议的分析指标
    3. 建议的时间范围
    4. 详细的数据分析思路"""
    
    # 构建用户提示词
    if headers and business_desc:
        user_prompt = f"""请基于以下信息提供分析建议：
        
        表头字段：{', '.join(headers)}
        业务描述：{business_desc}"""
    elif headers:
        user_prompt = f"""请基于以下表头字段提供分析建议：
        
        表头字段：{', '.join(headers)}"""
    else:
        user_prompt = f"""请基于以下业务描述提供分析建议：
        
        业务描述：{business_desc}"""
    
    # 调用ZhipuAI API
    response = client.chat.completions.create(
        model="glm-4-flash",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    
    return response.choices[0].message.content

def main():
    st.title("业务数据分析助手")
    st.write("这是一个帮助您进行业务数据分析的AI助手工具")
    
    # 文件上传部分
    uploaded_file = st.file_uploader("上传Excel文件（可选）", type=['xlsx', 'xls'])
    headers = None
    
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            headers = df.columns.tolist()
            st.success("成功读取表头信息！")
            st.write("检测到的表头字段：", headers)
        except Exception as e:
            st.error(f"读取文件时出错：{str(e)}")
    
    # 业务描述输入
    business_desc = st.text_area("请输入业务描述（可选）", height=100)
    
    # 验证输入
    if not headers and not business_desc:
        st.warning("请至少上传Excel文件或输入业务描述")
        return
    
    # 生成分析按钮
    if st.button("生成分析建议"):
        with st.spinner("AI正在分析中..."):
            try:
                analysis = get_ai_analysis(headers, business_desc)
                st.markdown("### AI分析建议")
                st.markdown(analysis)
            except Exception as e:
                st.error(f"生成分析建议时出错：{str(e)}")

if __name__ == "__main__":
    main() 