"""
文本模型封装模块，负责加载和管理文本大模型
使用Ollama运行Qwen2.5模型
"""
import os
import yaml
import json
import requests
from typing import Dict, List, Optional, Any
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from pydantic import BaseModel, Field

class TextAgent(LLM, BaseModel):
    """封装Ollama中的Qwen2.5模型为LangChain可用的LLM"""
    
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
    
    @property
    def _llm_type(self) -> str:
        """返回LLM类型"""
        return f"ollama_{self.model_name}"
    
    def _call(
        self, 
        prompt: str, 
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs
    ) -> str:
        """执行模型推理，调用Ollama API"""
        # 构建请求数据
        request_data = {
            "model": self.model_name,
            "prompt": prompt,
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

    @classmethod
    def from_config(cls, config_path: str = "config.yaml"):
        """从配置文件加载模型配置"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"配置文件 {config_path} 不存在")
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        model_config = config.get("models", {}).get("text", {})
        if not model_config:
            raise ValueError("配置文件中缺少文本模型配置")
            
        return cls(
            model_name=model_config.get("model_name", "qwen2.5:latest"),
            base_url=model_config.get("base_url", "http://localhost:11434"),
            api_key=model_config.get("api_key")
        )

# 测试代码
if __name__ == "__main__":
    # 从配置加载模型
    os.chdir("..")  # 切换到项目根目录，确保配置文件路径正确
    model = TextAgent.from_config()
    
    # 测试推理
    response = model("请介绍一下如何搭配正装")
    print(response)
