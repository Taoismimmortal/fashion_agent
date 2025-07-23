"""
MCP工具实现，用于提供标准化的模型调用接口
"""
import json
import yaml
import os
from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field

class MCPToolBase(BaseModel):
    """MCP工具基类"""
    
    name: str = Field(..., description="工具名称")
    description: str = Field(..., description="工具描述")
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具逻辑"""
        raise NotImplementedError("子类必须实现execute方法")
    
    def to_schema(self) -> Dict[str, Any]:
        """转换为MCP格式的工具描述"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.get_parameters_schema()
        }
    
    def get_parameters_schema(self) -> Dict[str, Any]:
        """获取工具参数schema"""
        # 默认实现，子类可以覆盖此方法提供更详细的schema
        return {
            "type": "object",
            "properties": {},
            "required": []
        }

class MCPToolRegistry:
    """MCP工具注册表，管理所有可用工具"""
    
    def __init__(self):
        self.tools: Dict[str, MCPToolBase] = {}
    
    def register(self, tool: MCPToolBase) -> None:
        """注册一个工具"""
        self.tools[tool.name] = tool
        print(f"工具 '{tool.name}' 已注册")
    
    def get_tool(self, name: str) -> Optional[MCPToolBase]:
        """获取指定名称的工具"""
        return self.tools.get(name)
    
    def list_tools(self) -> List[str]:
        """列出所有注册的工具名称"""
        return list(self.tools.keys())
    
    def get_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的schema定义"""
        return [tool.to_schema() for tool in self.tools.values()]
    
    def execute_tool(self, name: str, **kwargs) -> Dict[str, Any]:
        """执行指定的工具"""
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"未找到名为 '{name}' 的工具")
        
        return tool.execute(**kwargs)

# 创建全局工具注册表实例
tool_registry = MCPToolRegistry()

# 从配置文件加载MCP配置
def load_mcp_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """从配置文件加载MCP配置"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件 {config_path} 不存在")
        
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    return config.get("mcp", {})
