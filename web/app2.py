"""
Fashion Agent Web应用 

"""
import os
import sys
import json
import gradio as gr
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image
import time
import traceback

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from agents.fashion_agent import FashionAgent

class FashionWebApp:
    """Fashion Agent Web应用类 """
    
    def __init__(self):
        """初始化应用"""
        self.agent = None
        self.init_status = ""
        self.init_agent()
    
    def init_agent(self):
        """初始化Fashion Agent"""
        try:
            print("🚀 正在初始化Fashion Agent...")
            os.chdir(project_root)
            self.agent = FashionAgent()
            self.init_status = "✅ 系统已就绪"
            print("✅ Fashion Agent初始化成功")
        except Exception as e:
            error_msg = f"❌ 初始化失败: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            self.agent = None
            self.init_status = error_msg
    
    def get_system_status(self) -> str:
        """获取系统状态"""
        return self.init_status
    
    def analyze_uploaded_image(self, image: Image.Image) -> Dict[str, str]:
        """
        分析上传的图片并返回完整结果
        
        Args:
            image: 上传的PIL图片对象
            
        Returns:
            Dict[str, str]: 包含分析结果的字典
        """
        if not self.agent:
            return {
                "status": "error",
                "message": "系统未初始化，请刷新页面重试",
                "analysis": "",
                "recommendations": "",
                "products": ""
            }
        
        if image is None:
            return {
                "status": "error", 
                "message": "请先上传一张服装图片",
                "analysis": "",
                "recommendations": "", 
                "products": ""
            }
        
        try:
            # 保存临时图片
            temp_path = os.path.join(project_root, "web", "uploads", f"temp_{int(time.time())}.jpg")
            os.makedirs(os.path.dirname(temp_path), exist_ok=True)
            
            # 处理图片格式
            if image.mode in ('RGBA', 'LA', 'P'):
                # 转换为RGB格式
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                rgb_image.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
                image = rgb_image
            
            image.save(temp_path, "JPEG", quality=85)
            print(f"📸 开始分析图片: {temp_path}")
            
            # 调用agent分析
            result = self.agent.analyze_and_recommend(temp_path)
            
            if "error" in result:
                return {
                    "status": "error",
                    "message": f"分析过程出错: {result['error']}",
                    "analysis": "",
                    "recommendations": "",
                    "products": ""
                }
            
            # 提取和格式化结果
            image_analysis = result.get("image_analysis", "")
            recommendations = result.get("recommendations", "")
            product_suggestions = result.get("product_suggestions", {})
            
            # 格式化输出
            formatted_analysis = self._format_analysis_text(image_analysis)
            formatted_recommendations = self._format_recommendations_text(recommendations)
            formatted_products = self._create_product_cards(product_suggestions)
            
            # 清理临时文件
            try:
                os.remove(temp_path)
            except:
                pass
            
            return {
                "status": "success",
                "message": "分析完成！",
                "analysis": formatted_analysis,
                "recommendations": formatted_recommendations,
                "products": formatted_products
            }
            
        except Exception as e:
            error_msg = f"图片分析出错: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return {
                "status": "error",
                "message": error_msg,
                "analysis": "",
                "recommendations": "",
                "products": ""
            }
    
    def process_fashion_query(self, query: str) -> Dict[str, str]:
        """
        处理时尚相关的文本查询
        
        Args:
            query: 用户输入的查询文本
            
        Returns:
            Dict[str, str]: 包含回答和推荐的字典
        """
        if not self.agent:
            return {
                "status": "error",
                "message": "系统未初始化，请刷新页面重试",
                "answer": "",
                "products": ""
            }
        
        if not query or not query.strip():
            return {
                "status": "error",
                "message": "请输入您的时尚问题",
                "answer": "",
                "products": ""
            }
        
        try:
            print(f"💭 处理查询: {query}")
            
            # 调用agent处理查询
            result = self.agent.process_text_query(query.strip())
            
            if "error" in result:
                return {
                    "status": "error", 
                    "message": f"查询处理出错: {result['error']}",
                    "answer": "",
                    "products": ""
                }
            
            # 提取结果
            analysis = result.get("analysis", "")
            recommendations = result.get("recommendations", {})
            
            # 格式化输出
            formatted_answer = self._format_query_answer(analysis)
            formatted_products = self._create_product_cards(recommendations)
            
            return {
                "status": "success",
                "message": "查询完成！",
                "answer": formatted_answer,
                "products": formatted_products
            }
            
        except Exception as e:
            error_msg = f"文本查询出错: {str(e)}"
            print(error_msg)
            print(traceback.format_exc())
            return {
                "status": "error",
                "message": error_msg,
                "answer": "",
                "products": ""
            }
    
    def _format_analysis_text(self, text: str) -> str:
        """格式化图片分析文本"""
        if not text:
            return "暂无分析结果"
        
        # 简单的文本格式化
        formatted = f"""
## 🔍 服装分析结果

{text}

---
*分析完成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
        """.strip()
        
        return formatted
    
    def _format_recommendations_text(self, text: str) -> str:
        """格式化搭配建议文本"""
        if not text:
            return "暂无搭配建议"
        
        formatted = f"""
## 💡 专业搭配建议

{text}

---
*建议生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}*
        """.strip()
        
        return formatted
    
    def _format_query_answer(self, text: str) -> str:
        """格式化查询回答文本"""
        if not text:
            return "暂无回答内容"
        
        return text
    
    def _create_product_cards(self, products_data: Dict[str, Any]) -> str:
        """
        创建美观的商品卡片HTML
        
        Args:
            products_data: 商品数据字典
            
        Returns:
            str: 格式化的HTML字符串
        """
        if not products_data or not isinstance(products_data, dict):
            return self._create_empty_products_message()
        
        goods = products_data.get("goods", [])
        if not goods or not isinstance(goods, list):
            return self._create_empty_products_message()
        
        # 开始构建HTML
        html_parts = ["""
<div class="products-showcase">
    <div class="products-header">
        <h3>🛍️ 精选商品推荐</h3>
        <p class="products-count">为您找到 {count} 件相关商品</p>
    </div>
    <div class="products-grid">
""".format(count=len(goods))]
        
        # 处理每个商品
        for idx, item in enumerate(goods[:8]):  # 最多显示8个商品
            card_html = self._create_single_product_card(item, idx)
            html_parts.append(card_html)
        
        html_parts.append("""
    </div>
</div>
        """)
        
        # 添加CSS样式
        css_styles = self._get_product_cards_css()
        
        return css_styles + "".join(html_parts)
    
    def _create_single_product_card(self, item: Dict[str, Any], index: int) -> str:
        """创建单个商品卡片"""
        # 提取商品信息，提供默认值
        name = item.get("name", "未知商品")
        price = item.get("price", 0)
        coupon_price = item.get("coupon_price", 0)
        image_url = item.get("image", "")
        shop_name = item.get("shop_name", "未知店铺")
        good_comments_share = item.get("good_comments_share", 0)
        material_url = item.get("material_url", "#")
        
        # 处理商品名称（截断过长的名称）
        display_name = name[:50] + "..." if len(name) > 50 else name
        display_shop = shop_name[:15] + "..." if len(shop_name) > 15 else shop_name
        
        # 处理价格显示
        if price > 0:
            price_display = f"¥{price:.2f}"
            if coupon_price > 0 and coupon_price < price:
                coupon_display = f"<span class='coupon-price'>券后 ¥{coupon_price:.2f}</span>"
            else:
                coupon_display = ""
        else:
            price_display = "价格待询"
            coupon_display = ""
        
        # 处理图片URL
        if image_url:
            if not image_url.startswith("http"):
                image_url = f"https:{image_url}" if image_url.startswith("//") else f"https://{image_url}"
        else:
            image_url = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect width='200' height='200' fill='%23f0f0f0'/%3E%3Ctext x='100' y='100' text-anchor='middle' fill='%23999'%3E暂无图片%3C/text%3E%3C/svg%3E"
        
        # 处理好评率
        if good_comments_share > 0:
            if good_comments_share <= 1:
                rating_display = f"{good_comments_share*100:.0f}%"
            else:
                rating_display = f"{good_comments_share:.0f}%"
        else:
            rating_display = "暂无评价"
        
        # 处理商品链接
        if material_url and material_url != "#":
            if not material_url.startswith("http"):
                material_url = f"https://{material_url}"
            link_attrs = f'onclick="window.open(\'{material_url}\', \'_blank\')" style="cursor: pointer;"'
        else:
            link_attrs = 'style="cursor: default;"'
        
        # 构建卡片HTML
        card_html = f"""
        <div class="product-card" {link_attrs}>
            <div class="product-image-container">
                <img src="{image_url}" alt="{name}" class="product-image" 
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\\'http://www.w3.org/2000/svg\\' width=\\'200\\' height=\\'200\\'%3E%3Crect width=\\'200\\' height=\\'200\\' fill=\\'%23f0f0f0\\'/%3E%3Ctext x=\\'100\\' y=\\'100\\' text-anchor=\\'middle\\' fill=\\'%23999\\'%3E暂无图片%3C/text%3E%3C/svg%3E'" />
                <div class="product-overlay">
                    <span class="view-details">查看详情</span>
                </div>
            </div>
            <div class="product-info">
                <h4 class="product-title" title="{name}">{display_name}</h4>
                <div class="product-price-section">
                    <span class="product-price">{price_display}</span>
                    {coupon_display}
                </div>
                <div class="product-meta">
                    <div class="shop-info">
                        <span class="shop-icon">🏪</span>
                        <span class="shop-name">{display_shop}</span>
                    </div>
                    <div class="rating-info">
                        <span class="rating-icon">👍</span>
                        <span class="rating-value">{rating_display}</span>
                    </div>
                </div>
            </div>
        </div>
        """
        
        return card_html
    
    def _create_empty_products_message(self) -> str:
        """创建空商品提示消息"""
        return """
        <div class="empty-products">
            <div class="empty-icon">🛍️</div>
            <h3>暂无商品推荐</h3>
            <p>请尝试其他搜索关键词或稍后再试</p>
        </div>
        """
    
    def _get_product_cards_css(self) -> str:
        """获取商品卡片的CSS样式"""
        return """
<style>
.products-showcase {
    margin: 20px 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.products-header {
    text-align: center;
    margin-bottom: 30px;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 15px;
    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
}

.products-header h3 {
    margin: 0 0 10px 0;
    font-size: 24px;
    font-weight: 600;
}

.products-count {
    margin: 0;
    opacity: 0.9;
    font-size: 16px;
}

.products-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 25px;
    padding: 20px 0;
}

.product-card {
    background: white;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid #e5e7eb;
    position: relative;
}

.product-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.25);
    border-color: #667eea;
}

.product-image-container {
    position: relative;
    height: 220px;
    overflow: hidden;
    background: #f8fafc;
}

.product-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.product-card:hover .product-image {
    transform: scale(1.05);
}

.product-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(102, 126, 234, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.product-card:hover .product-overlay {
    opacity: 1;
}

.view-details {
    color: white;
    font-weight: 600;
    font-size: 16px;
    padding: 10px 20px;
    border: 2px solid white;
    border-radius: 25px;
    transition: all 0.3s ease;
}

.view-details:hover {
    background: white;
    color: #667eea;
}

.product-info {
    padding: 20px;
}

.product-title {
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    margin: 0 0 15px 0;
    line-height: 1.4;
    height: 44px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
}

.product-price-section {
    margin-bottom: 15px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.product-price {
    font-size: 20px;
    font-weight: 700;
    color: #dc2626;
}

.coupon-price {
    font-size: 12px;
    background: #dcfce7;
    color: #16a34a;
    padding: 4px 8px;
    border-radius: 6px;
    font-weight: 600;
}

.product-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 14px;
    color: #6b7280;
}

.shop-info, .rating-info {
    display: flex;
    align-items: center;
    gap: 6px;
}

.shop-icon, .rating-icon {
    font-size: 16px;
}

.shop-name {
    font-weight: 500;
    max-width: 100px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}

.rating-value {
    color: #059669;
    font-weight: 600;
}

.empty-products {
    text-align: center;
    padding: 80px 20px;
    color: #6b7280;
    background: #f9fafb;
    border-radius: 15px;
    border: 2px dashed #d1d5db;
}

.empty-icon {
    font-size: 64px;
    margin-bottom: 20px;
}

.empty-products h3 {
    font-size: 20px;
    color: #374151;
    margin: 0 0 10px 0;
}

.empty-products p {
    font-size: 16px;
    margin: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
    .products-grid {
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: 20px;
    }
    
    .product-card {
        border-radius: 12px;
    }
    
    .product-info {
        padding: 15px;
    }
    
    .product-title {
        font-size: 14px;
        height: 40px;
    }
    
    .product-price {
        font-size: 18px;
    }
    
    .products-header h3 {
        font-size: 20px;
    }
}

@media (max-width: 480px) {
    .products-grid {
        grid-template-columns: 1fr;
        gap: 15px;
    }
    
    .products-header {
        padding: 15px;
        margin-bottom: 20px;
    }
}
</style>
        """

def create_app_interface():
    """创建优化的Gradio界面"""
    app = FashionWebApp()
    
    # 主题和样式配置
    theme = gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="purple",
        neutral_hue="gray",
        font=[gr.themes.GoogleFont("Inter"), "Arial", "sans-serif"]
    )
    
    # 自定义CSS
    custom_css = """
    /* 全局样式 */
    .gradio-container {
        max-width: 1200px !important;
        margin: 0 auto !important;
        padding: 20px !important;
    }
    
    /* 主标题区域 */
    .app-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 40px 20px;
        border-radius: 20px;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 10px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .app-subtitle {
        font-size: 1.2rem;
        opacity: 0.9;
        margin: 0;
    }
    
    /* 状态指示器 */
    .status-indicator {
        display: inline-block;
        padding: 8px 16px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
        margin-bottom: 20px;
    }
    
    .status-success {
        background: #d1fae5;
        color: #065f46;
        border: 1px solid #10b981;
    }
    
    .status-error {
        background: #fee2e2;
        color: #991b1b;
        border: 1px solid #ef4444;
    }
    
    /* 标签页样式 */
    .tab-nav {
        border-radius: 15px;
        background: #f8fafc;
        padding: 8px;
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    /* 操作按钮 */
    .action-button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        border: none !important;
        border-radius: 12px !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 15px 30px !important;
        font-size: 16px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3) !important;
    }
    
    .action-button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* 快捷按钮 */
    .quick-btn {
        background: white !important;
        border: 2px solid #667eea !important;
        color: #667eea !important;
        border-radius: 25px !important;
        padding: 8px 16px !important;
        font-size: 14px !important;
        font-weight: 500 !important;
        margin: 4px !important;
        transition: all 0.3s ease !important;
    }
    
    .quick-btn:hover {
        background: #667eea !important;
        color: white !important;
        transform: translateY(-1px);
    }
    
    /* 输入区域 */
    .upload-area {
        border: 3px dashed #667eea !important;
        border-radius: 15px !important;
        background: rgba(102, 126, 234, 0.05) !important;
        transition: all 0.3s ease !important;
    }
    
    .upload-area:hover {
        border-color: #5a67d8 !important;
        background: rgba(102, 126, 234, 0.1) !important;
    }
    
    /* 结果区域 */
    .result-section {
        background: white;
        border-radius: 15px;
        padding: 25px;
        margin: 20px 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        border: 1px solid #e5e7eb;
    }
    
    /* 加载动画 */
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid #f3f3f3;
        border-top: 3px solid #667eea;
        border-radius: 50%;
        animation: spin 1s linear infinite;
        margin-right: 10px;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    /* 响应式设计 */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 10px !important;
        }
        
        .app-title {
            font-size: 2rem;
        }
        
        .app-subtitle {
            font-size: 1rem;
        }
        
        .app-header {
            padding: 30px 15px;
        }
    }
    """
    
    # 创建界面
    with gr.Blocks(theme=theme, css=custom_css, title="Fashion Agent 2.0") as interface:
        
        # 应用标题和状态
        gr.HTML("""
            <div class="app-header">
                <h1 class="app-title">🌟 Fashion Agent 2.0</h1>
                <p class="app-subtitle">AI驱动的智能时尚搭配助手</p>
            </div>
        """)
        
        # 系统状态显示
        with gr.Row():
            status_display = gr.HTML(value=f'<div class="status-indicator status-success">{app.get_system_status()}</div>')
        
        # 主要功能区域
        with gr.Tabs(elem_classes="tab-nav") as main_tabs:
            
            # 图片分析功能
            with gr.TabItem("📸 智能图片分析", id="image_tab"):
                gr.Markdown("### 🎯 上传服装图片，获取专业分析和搭配建议")
                
                with gr.Row():
                    # 左侧：图片上传和控制
                    with gr.Column(scale=1):
                        image_input = gr.Image(
                            type="pil",
                            label="📷 上传服装图片",
                            elem_classes="upload-area",
                            height=400
                        )
                        
                        analyze_btn = gr.Button(
                            "🔍 开始智能分析",
                            elem_classes="action-button",
                            size="lg"
                        )
                        
                        gr.Markdown("""
                        **💡 使用提示：**
                        - 上传清晰的服装图片效果更佳
                        - 支持 JPG、PNG 等常见格式
                        - 建议图片尺寸不超过 5MB
                        """)
                    
                    # 右侧：分析结果
                    with gr.Column(scale=1):
                        analysis_result = gr.Markdown(
                            value="请上传图片并点击分析按钮开始...",
                            label="🔍 图片分析结果",
                            elem_classes="result-section"
                        )
                
                # 搭配建议区域
                with gr.Row():
                    recommendations_result = gr.Markdown(
                        value="等待分析结果...",
                        label="💡 专业搭配建议",
                        elem_classes="result-section"
                    )
                
                # 商品推荐区域
                products_result = gr.HTML(
                    value='<div class="empty-products"><div class="empty-icon">🛍️</div><h3>等待分析结果</h3><p>完成图片分析后将为您推荐相关商品</p></div>'
                )
                
                # 绑定分析事件
                def handle_image_analysis(image):
                    """处理图片分析"""
                    if image is None:
                        return (
                            "❌ 请先上传图片",
                            "请先上传一张服装图片",
                            '<div class="empty-products"><div class="empty-icon">⚠️</div><h3>请先上传图片</h3></div>'
                        )
                    
                    # 显示处理中状态
                    processing_msg = "🔄 正在分析图片，请稍候..."
                    processing_html = '<div class="empty-products"><div class="empty-icon">⏳</div><h3>正在分析中...</h3><p>AI正在为您分析服装特征和搭配建议</p></div>'
                    
                    yield processing_msg, processing_msg, processing_html
                    
                    # 执行实际分析
                    result = app.analyze_uploaded_image(image)
                    
                    if result["status"] == "error":
                        error_html = f'<div class="empty-products"><div class="empty-icon">❌</div><h3>分析失败</h3><p>{result["message"]}</p></div>'
                        yield f"❌ {result['message']}", "分析失败，请重试", error_html
                    else:
                        yield result["analysis"], result["recommendations"], result["products"]
                
                analyze_btn.click(
                    fn=handle_image_analysis,
                    inputs=[image_input],
                    outputs=[analysis_result, recommendations_result, products_result]
                )
            
            # 文本查询功能
            with gr.TabItem("💬 时尚问答咨询", id="text_tab"):
                gr.Markdown("### 🤖 向AI时尚顾问提问，获取专业建议")
                
                # 快捷问题区域
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("#### 🔥 热门问题 (点击快速提问)")
                        quick_questions = [
                            "春季流行什么颜色和款式？",
                            "职场正装如何搭配？",
                            "约会穿什么比较合适？",
                            "休闲装怎么穿出时尚感？",
                            "如何根据体型选择服装？",
                            "秋冬外套推荐"
                        ]
                        
                        # 创建快捷按钮
                        quick_buttons = []
                        with gr.Row():
                            for i in range(0, len(quick_questions), 2):
                                with gr.Column():
                                    for j in range(2):
                                        if i + j < len(quick_questions):
                                            btn = gr.Button(
                                                quick_questions[i + j],
                                                elem_classes="quick-btn",
                                                size="sm"
                                            )
                                            quick_buttons.append((btn, quick_questions[i + j]))
                
                # 输入区域
                with gr.Row():
                    query_input = gr.Textbox(
                        label="💭 请输入您的时尚问题",
                        placeholder="例如：春天适合穿什么颜色？如何搭配职业装？约会穿什么好看？",
                        lines=3,
                        max_lines=5
                    )
                
                # 查询按钮
                with gr.Row():
                    query_btn = gr.Button(
                        "✨ 获取专业建议",
                        elem_classes="action-button",
                        size="lg"
                    )
                
                # 回答区域
                with gr.Row():
                    answer_result = gr.Markdown(
                        value="请输入您的问题，AI时尚顾问将为您提供专业建议...",
                        label="💡 专业时尚建议",
                        elem_classes="result-section"
                    )
                
                # 商品推荐区域
                text_products_result = gr.HTML(
                    value='<div class="empty-products"><div class="empty-icon">🛍️</div><h3>等待查询结果</h3><p>完成问题分析后将为您推荐相关商品</p></div>'
                )
                
                # 处理文本查询的函数
                def handle_text_query(query):
                    """处理文本查询"""
                    if not query or not query.strip():
                        return (
                            "❌ 请输入您的问题",
                            '<div class="empty-products"><div class="empty-icon">⚠️</div><h3>请输入问题</h3></div>'
                        )
                    
                    # 显示处理中状态
                    processing_msg = "🔄 正在分析您的问题并生成建议..."
                    processing_html = '<div class="empty-products"><div class="empty-icon">⏳</div><h3>正在思考中...</h3><p>AI正在为您分析问题并搜索相关商品</p></div>'
                    
                    yield processing_msg, processing_html
                    
                    # 执行实际查询
                    result = app.process_fashion_query(query)
                    
                    if result["status"] == "error":
                        error_html = f'<div class="empty-products"><div class="empty-icon">❌</div><h3>查询失败</h3><p>{result["message"]}</p></div>'
                        yield f"❌ {result['message']}", error_html
                    else:
                        yield result["answer"], result["products"]
                
                # 绑定查询事件
                query_btn.click(
                    fn=handle_text_query,
                    inputs=[query_input],
                    outputs=[answer_result, text_products_result]
                )
                
                # 支持回车提交
                query_input.submit(
                    fn=handle_text_query,
                    inputs=[query_input],
                    outputs=[answer_result, text_products_result]
                )
                
                # 绑定快捷按钮事件
                for btn, question in quick_buttons:
                    btn.click(
                        fn=lambda q=question: q,
                        outputs=[query_input]
                    )
        
        # 页脚信息
        gr.HTML("""
            <div style="margin-top: 50px; padding: 30px; text-align: center; background: #f8fafc; border-radius: 15px; border-top: 1px solid #e5e7eb;">
                <h4 style="color: #374151; margin-bottom: 20px; font-size: 18px;">🎯 功能特色</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px;">
                    <div style="text-align: center;">
                        <div style="font-size: 32px; margin-bottom: 10px;">🔍</div>
                        <h5 style="color: #4b5563; margin-bottom: 5px;">智能图片分析</h5>
                        <p style="color: #6b7280; font-size: 14px; margin: 0;">AI识别服装特征，提供专业分析</p>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 32px; margin-bottom: 10px;">💡</div>
                        <h5 style="color: #4b5563; margin-bottom: 5px;">专业搭配建议</h5>
                        <p style="color: #6b7280; font-size: 14px; margin: 0;">时尚顾问级别的搭配指导</p>
                    </div>
                    <div style="text-align: center;">
                        <div style="font-size: 32px; margin-bottom: 10px;">🛍️</div>
                        <h5 style="color: #4b5563; margin-bottom: 5px;">智能商品推荐</h5>
                        <p style="color: #6b7280; font-size: 14px; margin: 0;">精准匹配相关商品，一键购买</p>
                    </div>
                </div>
                <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; color: #6b7280; font-size: 14px;">
                    <p style="margin: 0;">✨ Fashion Agent 2.0 - 让AI成为您的专属时尚顾问</p>
                </div>
            </div>
        """)
    
    return interface

def main():
    """主函数 - 启动应用"""
    print("🚀 启动 Fashion Agent 2.0...")
    
    # 创建界面
    interface = create_app_interface()
    
    # 启动配置
    launch_config = {
        "server_name": "127.0.0.1",
        "server_port": 7861,  # 使用不同的端口避免冲突
        "show_api": False,
        "share": False,
        "inbrowser": True,
        "favicon_path": None,
        "show_error": True
    }
    
    print("📱 界面配置完成，正在启动服务...")
    print(f"🌐 访问地址: http://{launch_config['server_name']}:{launch_config['server_port']}")
    
    # 启动应用
    interface.launch(**launch_config)

if __name__ == "__main__":
    main()
