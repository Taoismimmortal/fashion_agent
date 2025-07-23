"""
Ollama 模型检查脚本
用于验证 Ollama 服务是否可用以及必要的模型是否已安装
"""
import os
import sys
import requests
import argparse
import time

def check_ollama_service(base_url="http://localhost:11434"):
    """检查Ollama服务是否可用"""
    try:
        response = requests.get(f"{base_url}/api/tags")
        if response.status_code == 200:
            print("✅ Ollama服务可用")
            return True
        else:
            print(f"❌ Ollama服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到Ollama服务 ({base_url}): {e}")
        print("请确保Ollama服务已启动，命令: 'ollama serve'")
        return False

def list_available_models(base_url="http://localhost:11434"):
    """列出所有可用的模型"""
    try:
        response = requests.get(f"{base_url}/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            if models:
                print("\n可用模型列表:")
                for i, model in enumerate(models, 1):
                    name = model.get("name", "未知")
                    size = model.get("size", 0) / (1024 * 1024 * 1024)  # 转换为GB
                    print(f"{i}. {name} (大小: {size:.2f} GB)")
            else:
                print("\n没有找到可用模型")
            return [model.get("name") for model in models]
        else:
            print(f"❌ 获取模型列表失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 获取模型列表出错: {e}")
        return []

def check_required_models(base_url="http://localhost:11434"):
    """检查项目所需的模型是否已安装"""
    required_models = {
        "qwen2:5b": "文本分析模型",
        "minicpm-v:8b-2.6-q4_K_M": "视觉分析模型"
    }
    
    available_models = list_available_models(base_url)
    
    print("\n项目所需模型检查:")
    all_available = True
    
    for model_name, description in required_models.items():
        if model_name in available_models:
            print(f"✅ {model_name} ({description}) - 已安装")
        else:
            print(f"❌ {model_name} ({description}) - 未安装")
            all_available = False
    
    return all_available

def pull_model(model_name, base_url="http://localhost:11434"):
    """拉取指定的模型"""
    print(f"正在拉取模型: {model_name}...")
    
    try:
        # 开始拉取模型
        response = requests.post(
            f"{base_url}/api/pull",
            json={"name": model_name, "stream": False}
        )
        
        if response.status_code == 200:
            print(f"✅ 模型 {model_name} 拉取成功")
            return True
        else:
            print(f"❌ 模型 {model_name} 拉取失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ 拉取模型时出错: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="检查Ollama服务和必要模型")
    parser.add_argument("--install", action="store_true", help="如果模型不可用，自动安装")
    parser.add_argument("--url", default="http://localhost:11434", help="Ollama API地址")
    
    args = parser.parse_args()
    
    print("=== Ollama 服务与模型检查 ===\n")
    
    # 检查Ollama服务
    if not check_ollama_service(args.url):
        print("\n请先启动Ollama服务，然后重新运行此脚本")
        sys.exit(1)
    
    # 检查所需模型
    all_models_available = check_required_models(args.url)
    
    # 如果指定了安装标志且有缺失模型，则拉取缺失的模型
    if not all_models_available and args.install:
        required_models = ["qwen2:5b", "minicpm-v:8b-2.6-q4_K_M"]
        available_models = list_available_models(args.url)
        
        print("\n开始拉取缺失的模型...")
        
        for model in required_models:
            if model not in available_models:
                pull_model(model, args.url)
                time.sleep(2)  # 稍作等待
        
        # 再次检查
        print("\n再次检查模型可用性...")
        check_required_models(args.url)
    
    print("\n=== 检查完成 ===")

if __name__ == "__main__":
    main()
