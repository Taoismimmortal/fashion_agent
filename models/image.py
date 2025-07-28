"""
视觉模型封装模块，负责图像理解和处理
使用Ollama运行MiniCPM-V 2.6模型
"""
import os
import yaml
import base64
import json
import requests
from typing import Dict, List, Optional, Any, Union
from PIL import Image
from pydantic import BaseModel, Field

class ImageModel(BaseModel):
    """封装Ollama中的MiniCPM-V视觉模型，提供图像理解功能"""
    
    model_name: str = Field(..., description="模型名称")
    base_url: str = Field("http://localhost:11434", description="Ollama API地址")
    api_key: Optional[str] = Field(None, description="API密钥（如果需要）")
    
    class Config:
        """Pydantic配置"""
        arbitrary_types_allowed = True
    
    def __init__(self, **kwargs):
        """初始化模型"""
        super().__init__(**kwargs)
        # 检查Ollama服务是否可用
        self._check_ollama_service()
    
    def _check_ollama_service(self):
        """检查Ollama服务是否可用"""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            if response.status_code == 200:
                available_models = response.json().get("models", [])
                model_names = [model.get("name") for model in available_models]
                
                # 检查模型是否已下载
                if self.model_name in model_names:
                    print(f"✅ 模型 {self.model_name} 已在Ollama中可用")
                else:
                    print(f"⚠️ 模型 {self.model_name} 在Ollama中不可用，将尝试在首次使用时拉取")
            else:
                print(f"⚠️ Ollama服务响应异常: {response.status_code}")
        except Exception as e:
            print(f"⚠️ 无法连接到Ollama服务 ({self.base_url}): {e}")
            print("请确保Ollama服务已启动，命令: 'ollama serve'")
    
    def _encode_image_to_base64(self, image_path_or_pil: Union[str, Image.Image]) -> str:
        """将图像编码为base64字符串

        Args:
            image_path_or_pil: 图像路径或PIL图像对象

        Returns:
            str: base64编码的图像
        """
        # 如果是路径，加载图像
        if isinstance(image_path_or_pil, str):
            if not os.path.exists(image_path_or_pil):
                raise FileNotFoundError(f"图像文件 {image_path_or_pil} 不存在")
            img = Image.open(image_path_or_pil)
        else:
            img = image_path_or_pil
        
        # 确保图像是RGB模式
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # 保存为临时内存中的JPEG
        import io
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        
        # 编码为base64
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def analyze_image(
        self, 
        image: Union[str, Image.Image],
        prompt: str = "描述这张图片中的服装，包括款式、颜色和风格",
        **kwargs
    ) -> str:
        """分析图像内容

        Args:
            image: 图像路径或PIL图像对象
            prompt: 引导模型关注的提示词
            **kwargs: 生成参数

        Returns:
            str: 图像分析结果
        """
        # 编码图像为base64
        try:
            image_base64 = self._encode_image_to_base64(image)
        except Exception as e:
            return f"图像编码失败: {str(e)}"
        
        # 构建请求数据
        request_data = {
            "model": self.model_name,
            "prompt": prompt,
            "images": [image_base64],
            "stream": False,
            "options": {}
        }
        
        # 添加生成参数
        if "temperature" in kwargs:
            request_data["options"]["temperature"] = kwargs["temperature"]
        if "top_p" in kwargs:
            request_data["options"]["top_p"] = kwargs["top_p"]
        if "max_tokens" in kwargs:
            request_data["options"]["num_predict"] = kwargs["max_tokens"]
        
        # 发送请求
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
                
            response = requests.post(
                f"{self.base_url}/api/generate",
                headers=headers,
                json=request_data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                error_msg = f"Ollama API错误: {response.status_code} - {response.text}"
                print(error_msg)
                return f"模型调用失败: {error_msg}"
        except Exception as e:
            error_msg = f"调用Ollama API时发生错误: {str(e)}"
            print(error_msg)
            return f"模型调用失败: {error_msg}"
    
    def analyze_fashion(
        self, 
        image: Union[str, Image.Image],
        task: str = "fashion_analysis"
    ) -> Dict[str, Any]:
        """分析时尚服装图像

        Args:
            image: 图像路径或PIL图像对象
            task: 分析任务类型 (fashion_analysis, matching_advice, style_detection, 
                  item_detection, comprehensive_analysis)

        Returns:
            Dict: 分析结果，包含多个方面的信息
        """
        prompts = {
            "fashion_analysis": "详细分析这张图片中的服装，包括款式、颜色、材质、品牌风格等。",
            "comprehensive_analysis": """
            对图片中的服装进行分析，只需要详细识别所有可见的服装单品：
            
            服装单品：详细识别所有可见的服装单品（如上衣、裤子、裙子、外套、鞋子等），包括颜色、款式、材质等细节。
            
            请以结构化方式提供分析，尽可能详细专业地描述所见到的服装单品。
            """
        }
        
        prompt = prompts.get(task, prompts["fashion_analysis"])
        
        # 获取文本分析结果
        analysis = self.analyze_image(image, prompt)
        result = {
            "raw_analysis": analysis,
            "task": task
        }
        
        return result
    
    @classmethod
    def from_config(cls, config_path: str = "config.yaml"):
        """从配置文件加载模型配置"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        model_config = config.get("models", {}).get("vision", {})
        if not model_config:
            raise ValueError("配置文件中缺少视觉模型配置")
            
        return cls(
            model_name=model_config.get("model_name", "minicpm-v:8b-2.6-q4_K_M"),
            base_url=model_config.get("base_url", "http://localhost:11434"),
            api_key=model_config.get("api_key")
        )

# 测试代码
if __name__ == "__main__":
    print(os.getcwd())
    os.chdir("..")  # 切换到项目根目录，确保配置文件路径正确
    # 从配置加载模型
    model = ImageModel.from_config()
    
    # 测试图像分析
    test_image_path = "web/example_images/test.png"  # 替换为实际测试图像路径
    if os.path.exists(test_image_path):
        result = model.analyze_fashion(test_image_path)
        print(result)
    else:
        print(f"测试图像 {test_image_path} 不存在，跳过测试")
