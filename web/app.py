"""
Fashion Agent Web应用
提供图片分析、文本查询和商品推荐功能
"""
import os
import sys
import json
import gradio as gr
from typing import Dict, Any, Optional, Tuple
from PIL import Image
import time

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from agents.fashion_agent import FashionAgent

class FashionWebApp:
    """Fashion Agent Web应用类"""
    
    def __init__(self):
        """初始化应用"""
        self.agent = None
        self.init_agent()
    
    def init_agent(self):
        """初始化Fashion Agent"""
        try:
            print("正在初始化Fashion Agent...")
            # 切换到项目根目录
            os.chdir(project_root)
            self.agent = FashionAgent()
            print("✅ Fashion Agent初始化成功")
        except Exception as e:
            print(f"❌ Fashion Agent初始化失败: {e}")
            self.agent = None
    
    def analyze_image_with_recommendations(self, image: Image.Image) -> Tuple[str, str, str]:
        """
        分析图片并提供搭配建议和商品推荐
        
        Args:
            image: 上传的图片
            
        Returns:
            Tuple[str, str, str]: (图片分析结果, 搭配建议, 商品推荐HTML)
        """
        if not self.agent:
            return "❌ 系统未初始化，请稍后重试", "", ""
        
        if image is None:
            return "❌ 请先上传图片", "", ""
        
        try:
            # 保存临时图片
            temp_path = os.path.join(project_root, "web", "uploads", "temp_upload.jpg")
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            image.save(temp_path, "JPEG")
            
            print(f"开始分析图片: {temp_path}")
            
            # 调用agent分析图片并获取推荐
            result = self.agent.analyze_and_recommend(temp_path)
            
            if "error" in result:
                return f"❌ 分析失败: {result['error']}", "", ""
            
            # 提取分析结果
            image_analysis = result.get("image_analysis", "未获取到图片分析结果")
            recommendations = result.get("recommendations", "未获取到搭配建议")
            product_suggestions = result.get("product_suggestions", {})
            
            # 格式化图片分析结果
            analysis_text = f"## 🔍 服装分析结果\n\n{image_analysis}"
            
            # 格式化搭配建议
            advice_text = f"## 💡 搭配建议\n\n{recommendations}"
            
            # 格式化商品推荐
            products_html = self._format_products_html(product_suggestions)
            
            return analysis_text, advice_text, products_html
            
        except Exception as e:
            error_msg = f"分析过程中出错: {str(e)}"
            print(error_msg)
            return f"❌ {error_msg}", "", ""
    
    def process_text_query(self, query: str) -> Tuple[str, str]:
        """
        处理文本查询
        
        Args:
            query: 用户查询文本
            
        Returns:
            Tuple[str, str]: (时尚建议, 商品推荐HTML)
        """
        if not self.agent:
            return "❌ 系统未初始化，请稍后重试", ""
        
        if not query.strip():
            return "❌ 请输入您的问题", ""
        
        try:
            print(f"处理文本查询: {query}")
            
            # 调用agent处理文本查询
            result = self.agent.process_text_query(query)
            
            if "error" in result:
                return f"❌ 查询失败: {result['error']}", ""
            
            # 提取分析结果
            analysis = result.get("analysis", "未获取到分析结果")
            recommendations = result.get("recommendations", {})
            
            # 格式化商品推荐
            products_html = self._format_products_html(recommendations)
            
            return analysis, products_html
            
        except Exception as e:
            error_msg = f"查询过程中出错: {str(e)}"
            print(error_msg)
            return f"❌ {error_msg}", ""
    
    def _format_products_html(self, products_data: Dict[str, Any]) -> str:
        """
        将商品数据格式化为HTML
        
        Args:
            products_data: 商品数据
            
        Returns:
            str: 格式化的HTML字符串
        """
        if not products_data or "goods" not in products_data:
            return "<div class='no-products'>暂无商品推荐</div>"
        
        goods = products_data.get("goods", [])
        if not goods:
            return "<div class='no-products'>暂无相关商品</div>"
        
        html_parts = ["<div class='products-container'>"]
        
        for item in goods:
            # 提取商品信息
            name = item.get("name", "未知商品")
            price = item.get("price", 0)
            coupon_price = item.get("coupon_price", 0)
            image_url = item.get("image", "")
            shop_name = item.get("shop_name", "未知店铺")
            good_comments_share = item.get("good_comments_share", 0)
            material_url = item.get("material_url", "#")
            
            # 处理价格显示
            price_str = f"¥{price:.2f}" if price > 0 else "价格面议"
            coupon_str = f"券后 ¥{coupon_price:.2f}" if coupon_price > 0 and coupon_price < price else ""
            
            # 处理图片URL
            if image_url and not image_url.startswith("http"):
                image_url = f"https:{image_url}" if image_url.startswith("//") else image_url
            
            # 处理好评率显示 - 修复数据问题
            if good_comments_share <= 1:
                good_rate_display = f"{good_comments_share*100:.0f}%" if good_comments_share > 0 else "暂无评价"
            else:
                good_rate_display = f"{good_comments_share:.0f}%" if good_comments_share > 0 else "暂无评价"
            
            # 构建可点击的商品卡片HTML - 使用正确的链接字段
            if material_url and material_url != "#":
                if not material_url.startswith("http"):
                    material_url = f"https://{material_url}"
                card_onclick = f"onclick=\"window.open('{material_url}', '_blank')\""
            else:
                card_onclick = ""
            card_cursor = "cursor: pointer;" if material_url != "#" else "cursor: default;"
            
            # 处理商品名称截断
            display_name = name[:45] + "..." if len(name) > 45 else name
            # 处理店铺名称截断
            display_shop_name = shop_name[:20] + "..." if len(shop_name) > 20 else shop_name
            
            # 构建图片HTML - 修复f-string中的反斜杠问题
            if image_url:
                # 创建默认图片的SVG（避免在f-string中使用反斜杠）
                default_image_svg = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f0f0f0'%3E%3C/rect%3E%3Ctext x='100' y='100' text-anchor='middle' dy='0.3em' font-family='Arial, sans-serif' font-size='14' fill='%23999'%3E暂无图片%3C/text%3E%3C/svg%3E"
                image_html = f"<img src='{image_url}' alt='{name}' onerror='this.src=\"{default_image_svg}\"' />"
            else:
                image_html = "<div class='no-image'>暂无图片</div>"
            
            # 构建商品卡片HTML
            card_html = f"""
            <div class='product-card' {card_onclick} style='{card_cursor}'>
                <div class='product-image'>
                    {image_html}
                </div>
                <div class='product-info'>
                    <h4 class='product-name' title='{name}'>{display_name}</h4>
                    <div class='product-price'>
                        <span class='current-price'>{price_str}</span>
                        {f"<span class='coupon-price'>{coupon_str}</span>" if coupon_str else ""}
                    </div>
                    <div class='product-meta'>
                        <div class='shop-info'>
                            <span class='shop-icon'>🏪</span>
                            <span class='shop-name'>{display_shop_name}</span>
                        </div>
                        <div class='rating-info'>
                            <span class='rating-icon'>👍</span>
                            <span class='rating'>{good_rate_display}</span>
                        </div>
                    </div>
                </div>
            </div>
            """
            
            html_parts.append(card_html)
        
        html_parts.append("</div>")
        
        # 优化的CSS样式
        css_style = """
        <style>
        .products-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            padding: 20px 0;
            max-height: 600px;
            overflow-y: auto;
        }
        .product-card {
            border: 1px solid #e1e5e9;
            border-radius: 16px;
            padding: 16px;
            background: white;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .product-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            border-color: #667eea;
        }
        .product-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
            opacity: 0;
            transition: opacity 0.3s ease;
        }
        .product-card:hover::before {
            opacity: 1;
        }
        .product-image {
            text-align: center;
            margin-bottom: 16px;
            border-radius: 12px;
            overflow: hidden;
        }
        .product-image img {
            width: 100%;
            height: 200px;
            object-fit: cover;
            transition: transform 0.3s ease;
        }
        .product-card:hover .product-image img {
            transform: scale(1.05);
        }
        .no-image {
            height: 200px;
            background: linear-gradient(135deg, #f5f7fa, #c3cfe2);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #6c757d;
            font-size: 14px;
        }
        .product-info {
            padding: 0;
        }
        .product-name {
            font-size: 16px;
            font-weight: 600;
            margin: 0 0 12px 0;
            color: #2c3e50;
            line-height: 1.4;
            height: 44px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
        }
        .product-price {
            margin-bottom: 16px;
            display: flex;
            align-items: baseline;
            gap: 8px;
        }
        .current-price {
            font-size: 20px;
            font-weight: 700;
            color: #e74c3c;
        }
        .coupon-price {
            font-size: 14px;
            color: #27ae60;
            background: #d5f4e6;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 500;
        }
        .product-meta {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }
        .shop-info, .rating-info {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 14px;
        }
        .shop-icon, .rating-icon {
            font-size: 16px;
        }
        .shop-name {
            color: #6c757d;
            font-weight: 500;
            max-width: 120px;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }
        .rating {
            color: #28a745;
            font-weight: 600;
        }
        .no-products {
            text-align: center;
            padding: 60px 20px;
            color: #6c757d;
            font-size: 16px;
            background: #f8f9fa;
            border-radius: 12px;
            border: 2px dashed #dee2e6;
        }
        .no-products::before {
            content: '🛍️';
            display: block;
            font-size: 48px;
            margin-bottom: 16px;
        }
        
        /* 响应式设计 */
        @media (max-width: 768px) {
            .products-container {
                grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
                gap: 16px;
            }
            .product-card {
                padding: 12px;
            }
            .product-name {
                font-size: 14px;
                height: 40px;
            }
            .current-price {
                font-size: 18px;
            }
            .shop-name {
                max-width: 80px;
            }
        }
        </style>
        """
        
        return css_style + "".join(html_parts)

def create_interface():
    """创建Gradio界面"""
    app = FashionWebApp()
    
    # 自定义CSS样式
    custom_css = """
    .gradio-container {
        max-width: 1400px !important;
        margin: 0 auto !important;
    }
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px 20px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    .main-header h1 {
        font-size: 2.5em;
        margin-bottom: 10px;
        font-weight: 700;
    }
    .main-header p {
        font-size: 1.2em;
        opacity: 0.9;
        margin: 0;
    }
    .tab-nav {
        background: #f8f9fa;
        border-radius: 15px;
        padding: 8px;
        margin-bottom: 20px;
    }
    .control-panel {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .upload-area {
        border: 3px dashed #667eea;
        border-radius: 15px;
        padding: 30px;
        text-align: center;
        transition: all 0.3s ease;
        background: rgba(102, 126, 234, 0.05);
    }
    .upload-area:hover {
        border-color: #5a67d8;
        background: rgba(102, 126, 234, 0.1);
    }
    .quick-question-btn {
        margin: 5px !important;
        border-radius: 20px !important;
        border: 1px solid #667eea !important;
        color: #667eea !important;
        background: white !important;
        transition: all 0.3s ease !important;
    }
    .quick-question-btn:hover {
        background: #667eea !important;
        color: white !important;
        transform: translateY(-1px);
    }
    .result-section {
        background: white;
        border-radius: 15px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e1e5e9;
    }
    """
    
    # 创建界面
    with gr.Blocks(css=custom_css, title="Fashion Agent - 智能时尚助手") as demo:
        # 标题区域
        gr.HTML("""
            <div class="main-header">
                <h1>🌟 Fashion Agent</h1>
                <p>智能时尚搭配助手 - AI驱动的服装分析与推荐</p>
            </div>
        """)
        
        with gr.Tabs(elem_classes="tab-nav") as tabs:
            # 图片分析标签页
            with gr.TabItem("📸 图片分析与推荐", id="image_analysis"):
                # 控制面板 - 按钮在上面
                with gr.Row(elem_classes="control-panel"):
                    with gr.Column():
                        gr.Markdown("### 🎯 操作面板")
                        analyze_btn = gr.Button(
                            "🔍 开始智能分析",
                            variant="primary",
                            size="lg",
                            scale=1
                        )
                        gr.Markdown("*上传服装图片，获得专业的搭配建议和商品推荐*")
                
                # 图片上传区域
                with gr.Row():
                    with gr.Column(scale=1):
                        image_input = gr.Image(
                            type="pil",
                            label="📷 上传服装图片",
                            elem_classes="upload-area",
                            height=400
                        )
                    
                    with gr.Column(scale=1):
                        # 分析结果区域
                        analysis_output = gr.Markdown(
                            label="🔍 图片分析结果",
                            value="请上传图片并点击分析按钮...",
                            elem_classes="result-section"
                        )
                
                # 搭配建议区域
                with gr.Row():
                    advice_output = gr.Markdown(
                        label="💡 专业搭配建议",
                        value="等待分析结果...",
                        elem_classes="result-section"
                    )
                
                # 商品推荐区域
                gr.Markdown("### 🛍️ 精选商品推荐")
                products_output = gr.HTML(
                    value="<div class='no-products'>等待分析结果，为您推荐相关商品</div>"
                )
                
                # 绑定事件
                analyze_btn.click(
                    fn=app.analyze_image_with_recommendations,
                    inputs=[image_input],
                    outputs=[analysis_output, advice_output, products_output]
                )
            
            # 文本查询标签页
            with gr.TabItem("💬 时尚咨询", id="text_query"):
                # 控制面板 - 按钮在上面
                with gr.Row(elem_classes="control-panel"):
                    with gr.Column(scale=2):
                        gr.Markdown("### 🤖 智能咨询")
                        query_btn = gr.Button(
                            "✨ 获取专业建议",
                            variant="primary",
                            size="lg"
                        )
                        gr.Markdown("*询问任何关于时尚搭配的问题，获得专业建议*")
                    
                    with gr.Column(scale=1):
                        gr.Markdown("#### 🔥 热门问题")
                        # 定义快捷问题和对应的按钮
                        quick_questions = [
                            "春季流行什么颜色？",
                            "职场穿搭推荐",
                            "约会服装搭配",
                            "休闲装怎么搭配？"
                        ]
                        
                        # 创建按钮列表，用于后续绑定事件
                        quick_buttons = []
                        for question in quick_questions:
                            btn = gr.Button(
                                question, 
                                size="sm",
                                elem_classes="quick-question-btn"
                            )
                            quick_buttons.append(btn)
                
                # 输入区域
                with gr.Row():
                    text_input = gr.Textbox(
                        label="💭 您的问题",
                        placeholder="例如：春天适合穿什么颜色的衣服？推荐几款适合上班的套装...",
                        lines=4,
                        max_lines=6
                    )
                
                # 回答区域
                with gr.Row():
                    advice_text_output = gr.Markdown(
                        label="💡 专业时尚建议",
                        value="请输入您的问题...",
                        elem_classes="result-section"
                    )
                
                # 商品推荐区域
                gr.Markdown("### 🛍️ 精选商品推荐")
                products_text_output = gr.HTML(
                    value="<div class='no-products'>请先提问，为您推荐相关商品</div>"
                )
                
                # 定义一个函数来设置文本输入框的值
                def set_question(question_text):
                    return question_text
                
                # 绑定快捷问题按钮事件 - 修复的版本
                for i, (question, btn) in enumerate(zip(quick_questions, quick_buttons)):
                    btn.click(
                        fn=lambda q=question: q,  # 使用闭包捕获当前问题
                        outputs=[text_input]
                    )
                
                # 绑定主要事件
                query_btn.click(
                    fn=app.process_text_query,
                    inputs=[text_input],
                    outputs=[advice_text_output, products_text_output]
                )
                
                # 支持回车键提交
                text_input.submit(
                    fn=app.process_text_query,
                    inputs=[text_input],
                    outputs=[advice_text_output, products_text_output]
                )
        
        # 页脚信息
        gr.HTML("""
            <div style="text-align: center; margin-top: 40px; padding: 30px; color: #6c757d; border-top: 1px solid #e1e5e9; background: #f8f9fa; border-radius: 15px;">
                <h4 style="color: #495057; margin-bottom: 15px;">💡 使用提示</h4>
                <p style="margin-bottom: 10px;">📸 上传清晰的服装图片可获得更准确的分析结果</p>
                <p style="margin-bottom: 10px;">🛍️ 点击商品卡片可直接跳转到购买页面</p>
                <p style="margin: 0;">✨ 支持各种时尚搭配问题咨询，让AI成为您的专属造型师</p>
            </div>
        """)
    
    return demo

def main():
    """主函数"""
    # 配置Gradio
    demo = create_interface()
    
    # 启动应用
    print("🚀 启动Fashion Agent Web应用...")
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        show_api=False,
        share=False,
        inbrowser=True
    )





if __name__ == "__main__":
    main()