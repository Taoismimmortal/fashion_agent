"""
Fashion Agent 主协调器
负责整合文本、图像和工具，提供完整的服务
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

# 导入京东工具
from agents.tools.jindon_tools import JdUnionGoodsQueryTool

# 注释掉 MCP 工具部分
# from agents.mcp_tools.base import tool_registry
# 确保工具被注册
# from agents.mcp_tools import taobao_integration, xiaohongshu_api, jingdong_tools

class FashionAgent:
    """时尚搭配智能体"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """初始化智能体"""
        # 加载配置
        self.config = self._load_config(config_path)
        
        # 初始化模型
        self.text_model = None
        self.vision_model = None
        
        # 初始化京东工具
        try:
            self.jd_tool = JdUnionGoodsQueryTool()
        except Exception as e:
            print(f"京东工具初始化失败: {e}")
            self.jd_tool = None
        
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
        
        # 使用京东工具搜索商品
        try:
            if self.jd_tool:
                try:
                    jd_results = self.jd_tool.run({
                        "keyword": query, 
                        "page_size": max_results
                    })

                    result = jd_results
                    print("成功获取京东商品推荐")

                except Exception as e:
                    print(f"执行京东工具时出错: {str(e)}")
            return result
        except Exception as e:
            return {"error": f"获取推荐时出错: {str(e)}"}

    def process_text_query(self, query: str) -> Dict[str, Any]:
        """处理文本查询，提供时尚分析和商品推荐"""
        if not self.text_model:
            return {"error": "文本模型未加载"}

        try:
            # 构建提示词，让模型分析并生成关键词
            prompt = f"""
                    你是一位专业的时尚搭配顾问，具有丰富的服装搭配经验和对时尚趋势的深度理解。请分析以下关于时尚搭配的问题，并提供专业、实用的建议。

                    用户问题：{query}

                    请按照以下格式详细回复：

                    ## 时尚分析
                    ### 风格定位
                    [分析用户需求的风格定位，如商务、休闲、约会、运动等]

                    ### 搭配建议
                    [详细的搭配建议，包括：
                    - 颜色搭配原则和推荐色彩
                    - 款式选择和版型建议
                    - 材质和面料推荐
                    - 配饰搭配技巧]

                    ### 场合适应性
                    [分析适合的穿着场合和季节特点]

                    ### 流行趋势
                    [结合当前时尚趋势给出建议]

                    ## 搜索关键词
                    keywords: [为商品搜索提供3-5个精准的关键词，用逗号分隔。关键词应该具体、实用，便于搜索到相关商品，如"春季外套,休闲西装,轻薄针织衫"]

                    请确保建议专业、实用，关键词精准有效。
"""

            # 调用文本模型获取分析
            analysis = self.text_model.invoke(prompt)

            # 提取搜索关键词
            keywords = ""
            if "搜索关键词" in analysis and "keywords:" in analysis:
                keyword_section = analysis.split("## 搜索关键词")[1].strip()
                keywords = keyword_section.split("keywords:")[
                    1].strip() if ":" in keyword_section else keyword_section.strip()

            result = {
                "analysis": analysis
            }

            # 如果有关键词且京东工具可用，则获取商品推荐
            if keywords and self.jd_tool:
                try:
                    # 使用提取的关键词搜索商品
                    jd_results = self.jd_tool.run({
                        "keyword": keywords,
                        "page_size": 5  # 获取5条商品信息
                    })

                    # 将商品信息添加到结果中
                    result["recommendations"] = jd_results
                    print(f"成功获取关键词'{keywords}'的商品推荐")
                except Exception as e:
                    print(f"获取商品推荐时出错: {str(e)}")
                    result["recommendation_error"] = str(e)

            return result
        except Exception as e:
            return {"error": f"处理文本查询时出错: {str(e)}"}

    def analyze_and_recommend(self, image_path: str) -> Dict[str, Any]:
        """分析图片并提供搭配建议和商品推荐"""
        if not os.path.exists(image_path):
            return {"error": f"图片 {image_path} 不存在"}

        if not self.vision_model:
            return {"error": "视觉模型未加载，无法分析图片"}

        if not self.text_model:
            return {"error": "文本模型未加载，无法生成建议"}

        try:
            # 1. 使用视觉模型分析图片
            vision_analysis = self.vision_model.analyze_fashion(
                image_path,
                "comprehensive_analysis"
            )

            image_analysis = vision_analysis["raw_analysis"]

            # 2. 使用文本模型生成搭配建议
            prompt = f"""
                    你是一位专业的时尚搭配顾问和服装分析师。请根据以下图片中的服装分析，提供专业的搭配建议和商品搜索关键词。

                    ## 图片分析结果
                    {image_analysis}

                    请按照以下格式提供专业建议：

                    ## 搭配建议
                    ### 现有单品分析
                    [分析图片中已有服装的优点和特色]

                    ### 搭配补充建议
                    [建议如何搭配其他单品来完善整体造型：
                    - 上下装搭配建议
                    - 颜色协调方案
                    - 配饰推荐（鞋子、包包、饰品等）
                    - 外套或内搭建议]

                    ### 风格提升
                    [如何通过搭配提升整体风格和时尚度]

                    ### 场合适配
                    [分析适合的穿着场合和如何调整搭配适应不同场合]

                    ## 搜索关键词
                    keywords: [基于图片分析和搭配建议，提供5-8个精准的商品搜索关键词，用逗号分隔。包括具体的服装类型、颜色、风格等，如"白色衬衫,高腰牛仔裤,休闲外套,棕色皮鞋,简约手表"]

                    请确保搭配建议实用可行，搜索关键词精准有效。
"""

            text_response = self.text_model.invoke(prompt)

            # 3. 提取搜索关键词
            search_terms = []
            if "搜索关键词" in text_response and "keywords:" in text_response:
                keyword_section = text_response.split("## 搜索关键词")[1].strip()
                keywords_str = keyword_section.split("keywords:")[
                    1].strip() if ":" in keyword_section else keyword_section.strip()
                search_terms = [term.strip() for term in keywords_str.split("、") if term.strip()]

            # 如果没有有效的关键词，使用默认关键词
            if not search_terms:
                search_terms = ["时尚", "服装"]

            # 4. 使用关键词搜索商品
            # product_suggestions = {}
            # if self.jd_tool:
            #     try:
            #         # 使用提取的第一个关键词搜索商品
            #         main_keyword = search_terms[0] if search_terms else "时尚服装"
            #         jd_results = self.jd_tool.run({
            #             "keyword": main_keyword,
            #             "page_size": 5  # 获取5条商品信息
            #         })

            #         product_suggestions["jd_recommendations"] = jd_results
            #         print(f"成功获取关键词'{main_keyword}'的商品推荐")
            #     except Exception as e:
            #         print(f"获取商品推荐时出错: {str(e)}")
            #         product_suggestions["error"] = str(e)
            product_suggestions = {}
            if self.jd_tool:
                try:
                    # 遍历多个关键词搜索商品，提高搜索成功率
                    all_goods = []
                    successful_keywords = []
                    
                    search_keywords = search_terms + ["衣服"] if search_terms else ["衣服"]
                    
                    for keyword in search_keywords:
                        try:
                            print(f"尝试搜索关键词: {keyword}")
                            jd_results = self.jd_tool.run({
                                "keyword": keyword.strip(),
                                "page_size": 5  
                            })
                            
                            # 检查是否有商品结果
                            if jd_results and "goods" in jd_results and jd_results["goods"]:
                                all_goods.extend(jd_results["goods"])
                                successful_keywords.append(keyword)
                                print(f"关键词'{keyword}'搜索成功，获得{len(jd_results['goods'])}个商品")
                                
                                # 如果已经有足够的商品，可以提前结束
                                if len(all_goods) >= 10:  # 目标获取6个商品
                                    break
                            else:
                                print(f"关键词'{keyword}'未找到商品")
                                
                        except Exception as keyword_error:
                            print(f"关键词'{keyword}'搜索出错: {str(keyword_error)}")
                            continue
                    
                    # 组装最终结果
                    if all_goods:
                        # 去重并限制数量
                        unique_goods = []
                        seen_names = set()
                        for good in all_goods:
                            name = good.get("name", "")
                            if name not in seen_names:
                                unique_goods.append(good)
                                seen_names.add(name)
                                if len(unique_goods) >= 6:  # 最多6个商品
                                    break
                        
                        product_suggestions = {
                            "goods": unique_goods,
                            "total": len(unique_goods),
                            "successful_keywords": successful_keywords,
                            "search_info": f"成功搜索关键词: {', '.join(successful_keywords)}"
                        }
                        print(f"总共获取{len(unique_goods)}个去重商品，使用关键词: {', '.join(successful_keywords)}")
                    else:
                        product_suggestions = {
                            "goods": [],
                            "total": 0,
                            "error": "所有关键词都未找到相关商品"
                        }
                        print("所有关键词搜索都失败")
                        
                except Exception as e:
                    print(f"商品搜索过程出错: {str(e)}")
                    product_suggestions = {"error": str(e)}

            # 5. 组合结果
            result = {
                "image_analysis": image_analysis,
                "recommendations": text_response.split("## 搭配建议")[1].split("## 搜索关键词")[
                    0].strip() if "## 搭配建议" in text_response else text_response,
                "search_terms": search_terms,
                "product_suggestions": product_suggestions
            }

            return result
        except Exception as e:
            return {"error": f"分析过程中出错: {str(e)}"}
# 测试代码
if __name__ == "__main__":
    os.chdir("..")  # 切换到项目根目录，确保配置文件路径正确
    import json

    # 实例化 FashionAgent
    agent = FashionAgent()

    # 测试不同类型的查询
    test_queries = [
        "春天适合穿什么颜色的衣服？",
        "推荐几款适合春季的外套",

    ]

    for query in test_queries:
        print(f"\n测试查询: {query}")
        result = agent.process_text_query(query)
        print("\n时尚建议:")
        print(result)

