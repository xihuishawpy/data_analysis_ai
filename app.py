import streamlit as st
from zhipuai import ZhipuAI
import pandas as pd
from typing import Optional, List, Dict
from PIL import Image
import io
import base64

# 配置ZhipuAI API
client = ZhipuAI(api_key="")

def extract_headers_from_image(image_bytes: bytes) -> List[str]:
    """
    使用智谱AI的视觉模型从图片中提取表头
    """
    try:
        # 将图片转换为base64编码
        img_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        response = client.chat.completions.create(
            model="glm-4v-flash",  
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": img_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": "请识别图片中的表头字段，将所有表头字段用逗号分隔列出来。只需要返回表头字段，不需要其他解释。"
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        headers_text = response.choices[0].message.content
        # 清理并分割表头文本
        headers = [h.strip() for h in headers_text.split(',')]
        return headers
    except Exception as e:
        raise Exception(f"图片识别失败：{str(e)}")

def get_ai_analysis(headers: Optional[List[str]] = None, business_desc: Optional[str] = None, 
                    temperature: float = 0.7, top_p: float = 0.7, max_tokens: int = 2000) -> str:
    """
    获取AI分析建议
    Args:
        headers: 表头字段列表
        business_desc: 业务描述
        temperature: 温度参数，控制输出的随机性
        top_p: 核采样参数
        max_tokens: 最大生成token数
    """
    # 构建系统提示词
    system_prompt = """你是第三方检测公司的专业的数据分析专家，仅基于用户提供的信息给出详细的分析建议。
    分析建议应该包含以下方面：
    1. 建议的数据分析维度
    2. 建议的分析指标
    3. 根据建议的维度和指标，分主题给出详细的数据分析思路
    4. 对每个主题具体的维度、指标进行指导
    5. 如果可以，进一步对主题进行详细的交叉分析
    """
    
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
        ],
        temperature=temperature,
        top_p=top_p,
        max_tokens=max_tokens
    )
    
    return response.choices[0].message.content

def main():
    st.title("业务数据分析助手")
    
    # 添加应用介绍
    with st.expander("📖 关于本应用", expanded=False):
        st.markdown("""
        ### 🎯 应用功能
        本应用是一个智能数据分析助手，可以帮助您：
        - 📊 快速分析数据表结构
        - 🎯 提供专业的数据分析建议
        - 📈 生成详细的分析思路和方案
        - 🔍 识别关键分析维度和指标
        
        ### 💡 使用方法
        1. **数据输入**（至少选择一种）：
           - 上传Excel/CSV文件：系统将自动读取表头信息
           - 上传表头截图：系统将自动识别表头字段
           - 输入业务描述：描述您的业务场景和分析需求
        
        2. **参数调节**（可选）：
           - 在左侧边栏调整模型参数，影响输出结果的特性
        
        3. **生成分析**：
           - 点击"生成分析建议"按钮获取AI分析建议
           - 系统将从多个维度为您提供专业的分析方案
        
        ### ⚙️ 参数说明
        - **Temperature**：控制输出的随机性，值越小结果越稳定
        - **Top P**：控制输出的多样性，值越小更保守
        - **Max Tokens**：控制输出的最大长度
        """)
    
    st.write("这是一个帮助您进行业务数据分析的AI助手工具")
    
    # 添加侧边栏用于模型参数调节
    with st.sidebar:
        st.header("模型参数设置")
        temperature = st.slider(
            "Temperature (温度)",
            min_value=0.0,
            max_value=1.0,
            value=0.4,
            help="控制输出的随机性，值越大输出越随机，值越小输出越确定"
        )
        
        top_p = st.slider(
            "Top P (核采样)",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            help="控制词的采样范围，值越小生成的文本越保守"
        )
        
        max_tokens = st.number_input(
            "Max Tokens (最大生成长度)",
            min_value=100,
            max_value=8000,
            value=2500,
            help="控制生成文本的最大长度"
        )
    
    # 文件上传部分
    st.subheader("数据输入")
    upload_type = st.radio(
        "选择上传方式",
        ["文件上传", "图片识别"],
        horizontal=True
    )
    
    headers = None
    
    if upload_type == "文件上传":
        uploaded_file = st.file_uploader(
            "上传Excel/CSV文件（可选）", 
            type=['xlsx', 'xls', 'csv']
        )
        
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                headers = df.columns.tolist()
                st.success("成功读取表头信息！")
                st.write("检测到的表头字段：", headers)
            except Exception as e:
                st.error(f"读取文件时出错：{str(e)}")
    
    else:  # 图片识别
        uploaded_image = st.file_uploader(
            "上传表头截图（可选）",
            type=['png', 'jpg', 'jpeg']
        )
        
        if uploaded_image:
            try:
                # 显示上传的图片
                image = Image.open(uploaded_image)
                st.image(image, caption="上传的表头截图", use_column_width=True)
                
                # 转换图片为bytes
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format=image.format)
                img_byte_arr = img_byte_arr.getvalue()
                
                # 识别表头
                with st.spinner("正在识别表头..."):
                    headers = extract_headers_from_image(img_byte_arr)
                    st.success("成功识别表头信息！")
                    st.write("识别到的表头字段：", headers)
            except Exception as e:
                st.error(f"图片识别失败：{str(e)}")
    
    # 业务描述输入
    business_desc = st.text_area("请输入业务描述（可选）", height=100)
    
    # 验证输入
    if not headers and not business_desc:
        st.warning("请至少上传Excel文件或输入业务描述")
        return
    
    # 生成分析按钮
    if st.button("生成分析建议"):
        with st.spinner("正在分析中..."):
            try:
                analysis = get_ai_analysis(
                    headers, 
                    business_desc,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens
                )
                st.markdown("### AI分析建议")
                st.markdown(analysis)
            except Exception as e:
                st.error(f"生成分析建议时出错：{str(e)}")

if __name__ == "__main__":
    main() 