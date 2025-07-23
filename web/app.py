"""
Web界面模块 - 基于Gradio构建的时尚搭配助手界面
"""
import os
import sys
import json
import gradio as gr
from PIL import Image
import numpy as np

# 调整当前工作目录确保能正确导入项目模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.fashion_agent import FashionAgent

# 初始化Fashion Agent
agent = FashionAgent()

def save_uploaded_image(image):
    """保存上传的图片到临时文件"""
    if image is None:
        return None
    
    # 确保example_images目录存在
    os.makedirs("web/example_images", exist_ok=True)
    
    # 将图片保存为临时文件
    temp_path = "web/example_images/temp_upload.jpg"
    
    # 如果是numpy数组（从Gradio传入）转换为PIL Image
    if isinstance(image, np.ndarray):
        pil_image = Image.fromarray(image)
        pil_image.save(temp_path)
    else:
        # 假设是文件路径
        image.save(temp_path)
    
    return temp_path

def analyze_image(image):
    """处理图片分析请求"""
    if image is None:
        return "请上传图片", "请先上传一张包含服装的图片进行分析", None
    
    try:
        # 保存图片
        image_path = save_uploaded_image(image)
        
        # 分析图片
        result = agent.process_image(image_path)
        
        if "error" in result:
            return "处理出错", f"分析过程中出现错误: {result['error']}", None
        
        # 返回分析结果
        analysis = result.get("analysis", "无法获取分析结果")
        
        return "图片分析完成", analysis, image
    except Exception as e:
        return "处理出错", f"分析过程中出现异常: {str(e)}", None

def get_fashion_recommendations(image):
    """获取时尚搭配建议和商品推荐"""
    if image is None:
        return "请上传图片", "请先上传一张包含服装的图片获取搭配建议", None, None, None
    
    try:
        # 保存图片
        image_path = save_uploaded_image(image)
        
        # 获取全面分析和建议
        result = agent.analyze_and_recommend(image_path)
        
        if "error" in result:
            return "处理出错", f"分析过程中出现错误: {result['error']}", None, None, None
        
        # 提取结果
        image_analysis = result.get("image_analysis", "无法获取图片分析")
        recommendations = result.get("recommendations", "无法获取搭配建议")
        
        # 格式化产品推荐
        product_suggestions = result.get("product_suggestions", {})
        
        # 提取淘宝商品推荐
        taobao_products = product_suggestions.get("product_recommendations", [])
        if isinstance(taobao_products, list) and taobao_products:
            taobao_html = "<h3>👕 推荐商品</h3><ul>"
            for product in taobao_products:
                name = product.get("name", "未知商品")
                price = product.get("price", "未知价格")
                link = product.get("link", "#")
                taobao_html += f'<li><a href="{link}" target="_blank">{name} - ¥{price}</a></li>'
            taobao_html += "</ul>"
        else:
            taobao_html = "<p>暂无商品推荐</p>"
        
        # 提取小红书搭配灵感
        xhs_inspirations = product_suggestions.get("outfit_inspirations", [])
        if isinstance(xhs_inspirations, list) and xhs_inspirations:
            xhs_html = "<h3>✨ 搭配灵感</h3><ul>"
            for inspiration in xhs_inspirations:
                title = inspiration.get("title", "未知灵感")
                author = inspiration.get("author", "未知作者")
                link = inspiration.get("link", "#")
                xhs_html += f'<li><a href="{link}" target="_blank">{title} - by {author}</a></li>'
            xhs_html += "</ul>"
        else:
            xhs_html = "<p>暂无搭配灵感</p>"
        
        return "分析完成", recommendations, image, taobao_html, xhs_html
    except Exception as e:
        return "处理出错", f"分析过程中出现异常: {str(e)}", None, None, None

def process_text_query(query):
    """处理文本查询"""
    if not query or query.strip() == "":
        return "请输入查询内容", None, None
    
    try:
        # 处理文本查询
        result = agent.process_text_query(query)
        
        if "error" in result:
            return f"处理出错: {result['error']}", None, None
        
        # 获取回复和推荐
        advice = result.get("advice", "无法获取建议")
        
        # 格式化产品推荐
        recommendations = result.get("recommendations", {})
        
        # 提取淘宝商品推荐
        taobao_products = recommendations.get("product_recommendations", [])
        if isinstance(taobao_products, list) and taobao_products:
            taobao_html = "<h3>👕 推荐商品</h3><ul>"
            for product in taobao_products:
                name = product.get("name", "未知商品")
                price = product.get("price", "未知价格")
                link = product.get("link", "#")
                taobao_html += f'<li><a href="{link}" target="_blank">{name} - ¥{price}</a></li>'
            taobao_html += "</ul>"
        else:
            taobao_html = "<p>暂无商品推荐</p>"
        
        # 提取小红书搭配灵感
        xhs_inspirations = recommendations.get("outfit_inspirations", [])
        if isinstance(xhs_inspirations, list) and xhs_inspirations:
            xhs_html = "<h3>✨ 搭配灵感</h3><ul>"
            for inspiration in xhs_inspirations:
                title = inspiration.get("title", "未知灵感")
                author = inspiration.get("author", "未知作者")
                link = inspiration.get("link", "#")
                xhs_html += f'<li><a href="{link}" target="_blank">{title} - by {author}</a></li>'
            xhs_html += "</ul>"
        else:
            xhs_html = "<p>暂无搭配灵感</p>"
        
        return advice, taobao_html, xhs_html
    except Exception as e:
        return f"处理查询时出现异常: {str(e)}", None, None

# 创建Gradio界面
with gr.Blocks(title="AI时尚搭配助手", theme=gr.themes.Soft(primary_hue="indigo")) as demo:
    gr.Markdown(
    """
    # 🌟 AI 时尚搭配助手 🌟
    
    上传服装图片获取专业分析和搭配建议，或直接提问你的时尚疑问！
    
    *由MiniCPM-V视觉模型和Qwen2文本模型提供支持*
    """
    )
    
    with gr.Tabs():
        # 图片分析标签页
        with gr.TabItem("👔 图片分析", id=1):
            with gr.Row():
                with gr.Column(scale=1):
                    image_input = gr.Image(type="pil", label="上传服装图片")
                    with gr.Row():
                        analyze_btn = gr.Button("🔍 分析图片", variant="primary")
                        recommend_btn = gr.Button("✨ 获取搭配建议", variant="secondary")
                
                with gr.Column(scale=2):
                    result_heading = gr.Textbox(label="", value="上传图片后点击按钮进行分析")
                    result_text = gr.Markdown(label="分析结果")
            
            # 只在搭配建议时显示的部分
            with gr.Row(visible=False) as recommendation_row:
                with gr.Column(scale=1):
                    taobao_recommendations = gr.HTML(label="商品推荐")
                
                with gr.Column(scale=1):
                    xhs_inspirations = gr.HTML(label="搭配灵感")
        
        # 文本咨询标签页
        with gr.TabItem("💬 时尚咨询", id=2):
            with gr.Row():
                text_query = gr.Textbox(label="输入你的时尚问题", lines=3, placeholder="例如：我想找适合夏天的办公室穿搭...")
                query_btn = gr.Button("🔍 获取建议", variant="primary")
            
            with gr.Row():
                advice_text = gr.Markdown(label="时尚建议")
            
            with gr.Row():
                with gr.Column(scale=1):
                    text_taobao_recommendations = gr.HTML(label="商品推荐")
                
                with gr.Column(scale=1):
                    text_xhs_inspirations = gr.HTML(label="搭配灵感")
    
    # 设置事件处理
    analyze_btn.click(
        analyze_image, 
        inputs=[image_input], 
        outputs=[result_heading, result_text, image_input]
    )
    
    recommend_btn.click(
        get_fashion_recommendations,
        inputs=[image_input],
        outputs=[result_heading, result_text, image_input, taobao_recommendations, xhs_inspirations],
    ).then(
        lambda: gr.update(visible=True),
        None,
        [recommendation_row]
    )
    
    query_btn.click(
        process_text_query,
        inputs=[text_query],
        outputs=[advice_text, text_taobao_recommendations, text_xhs_inspirations]
    )

if __name__ == "__main__":
    # 设置示例图片目录
    os.makedirs("web/example_images", exist_ok=True)
    
    # 启动Gradio应用
    demo.launch(share=False)
