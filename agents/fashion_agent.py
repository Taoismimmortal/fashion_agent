"""
Fashion Agent 主协调器
负责整合文本、图像和MCP工具，提供完整的服务
"""
import os
import yaml
import json
from typing import Dict, List, Any, Optional
from PIL import Image
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from models.text_agent import TextAgent
from models.image import ImageModel

from agents.mcp_tools.base import tool_registry
# 确保工具被注册
from agents.mcp_tools import taobao_integration, xiaohongshu_api

class FashionAgent:
    """时尚搭配智能体"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化智能体"""
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化模型
        self.text_model = None
        self.vision_model = None
        
        # 完成初始化
        self._initialize()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        return config
    
    def _initialize(self):
        """初始化模型和工具"""
        print("正在初始化Fashion Agent...")
        
        # 初始化文本模型
        try:
            print("加载文本模型...")
            self.text_model = TextAgent.from_config()
        except Exception as e:
            print(f"文本模型加载失败: {e}")
        
        # 初始化视觉模型
        try:
            print("加载视觉模型...")
            self.vision_model = ImageModel.from_config()
        except Exception as e:
            print(f"视觉模型加载失败: {e}")
        
        print("Fashion Agent 初始化完成")
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """处理服装图片，返回完整分析结果"""
        if not os.path.exists(image_path):
            return {"error": f"图片 {image_path} 不存在"}
            
        if not self.vision_model:
            return {"error": "视觉模型未加载，无法分析图片"}
        
        try:
            comprehensive_analysis = self.vision_model.analyze_fashion(
                image_path, 
                "comprehensive_analysis"
            )
            
            return {"analysis": comprehensive_analysis["raw_analysis"]}
        except Exception as e:
            return {"error": f"分析图片时出错: {str(e)}"}
    
    def get_recommendations(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """获取商品推荐和搭配灵感"""
        result = {}
        
        # 获取淘宝商品推荐
        try:
            taobao_tool = tool_registry.get_tool("taobao_product_search")
            if taobao_tool:
                result["product_recommendations"] = taobao_tool.execute(
                    keywords=query, 
                    max_results=max_results
                )
            
            # 获取小红书搭配灵感
            xhs_tool = tool_registry.get_tool("xiaohongshu_outfit_search")
            if xhs_tool:
                result["outfit_inspirations"] = xhs_tool.execute(
                    keywords=query, 
                    max_results=max_results
                )
            
            return result
        except Exception as e:
            return {"error": f"获取推荐时出错: {str(e)}"}
    
    def process_text_query(self, query: str) -> Dict[str, Any]:
        """处理文本查询，返回合适的回复"""
        if not self.text_model:
            return {"error": "文本模型未加载，无法处理查询"}
        
        try:
            prompt = f"""
            用户查询: {query}
            
            请提供专业、详细且有帮助的时尚建议回复。考虑:
            1. 回答用户的核心问题
            2. 提供具体的服装搭配建议
            3. 可能的颜色搭配
            4. 适合的场合
            5. 注意事项
            
            请像一位专业的时尚顾问一样回答。
            """
            
            # 使用文本模型生成回复
            advice = self.text_model.invoke(prompt)
            
            # 如果查询包含商品需求，添加推荐
            if any(keyword in query for keyword in ["推荐", "购买", "哪里买", "商品", "链接"]):
                recommendations = self.get_recommendations(query)
                return {
                    "advice": advice,
                    "recommendations": recommendations
                }
            
            return {"advice": advice}
        except Exception as e:
            return {"error": f"处理文本查询时出错: {str(e)}"}
    
    def analyze_and_recommend(self, image_path: str) -> Dict[str, Any]:
        """基于图片分析提供搭配建议和商品推荐
        
        这个方法结合了图像分析和商品推荐功能，提供完整的搭配方案
        """
        if not os.path.exists(image_path):
            return {"error": f"图片 {image_path} 不存在"}
            
        if not self.vision_model or not self.text_model:
            return {"error": "模型未完全加载，无法提供完整分析"}
        
        try:
            # 获取图像分析结果
            print("分析图片中的服装...")
            image_result = self.process_image(image_path)
            
            if "error" in image_result:
                return image_result
                
            image_analysis = image_result.get("analysis", "")
            
            # 使用强大的提示词让文本模型处理所有复杂逻辑
            print("生成搭配建议...")
            recommendation_prompt = f"""
            你是一位专业的时尚搭配顾问。根据以下图片分析，提供完整的搭配建议：
            
            图片分析: {image_analysis}
            
            请提供以下信息：
            1. 风格总结：概括图片中服装的整体风格和特点
            2. 搭配建议：如何改进或完善当前搭配
            3. 替代方案：2-3套可以参考的替代搭配方案
            4. 配饰推荐：适合添加的配饰建议
            5. 场合建议：适合的场合和注意事项
            6. 购物关键词：用于搜索相似或匹配商品的5-8个关键词
            
            确保你的建议专业、具体且实用，能够帮助用户提升整体造型效果。
            """
            
            # 使用文本模型生成全面的建议
            full_recommendation = self.text_model.invoke(recommendation_prompt)
            
            # 从建议中提取购物关键词
            search_terms = []
            try:
                if "关键词" in full_recommendation and ":" in full_recommendation:
                    keywords_section = full_recommendation.split("关键词")[1].split("\n")[0]
                    potential_terms = keywords_section.split(":")[-1].strip()
                    search_terms = [term.strip() for term in potential_terms.split(",") if term.strip()]
            except:
                # 提取失败则使用默认词
                search_terms = ["时尚", "搭配"]
            
            # 构建搜索查询
            search_query = " ".join(search_terms) if search_terms else "时尚服装搭配"
            
            # 获取相关商品推荐
            print("查找相关商品推荐...")
            product_recommendations = self.get_recommendations(search_query)
            
            # 返回完整结果
            return {
                "image_analysis": image_analysis,
                "recommendations": full_recommendation,
                "search_terms": search_terms,
                "product_suggestions": product_recommendations
            }
            
        except Exception as e:
            return {"error": f"分析和推荐过程中出错: {str(e)}"}


# 测试代码
if __name__ == "__main__":
    try:
        agent = FashionAgent()
        
        # 测试图像处理
        test_image_path = "web/example_images/test.png"  # 替换为实际测试图像路径
        if os.path.exists(test_image_path):
            print("测试图像分析...")
            result = agent.process_image(test_image_path)
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # 测试图像分析+搭配建议
            print("\n测试基于图像的搭配建议...")
            outfit_recommendation = agent.analyze_and_recommend(test_image_path)
            print(json.dumps(outfit_recommendation, indent=2, ensure_ascii=False))
        
        # 测试文本查询
        print("\n测试文本查询...")
        query = "我想找一套适合参加婚礼的正装"
        result = agent.process_text_query(query)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
