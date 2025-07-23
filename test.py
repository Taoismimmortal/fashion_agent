"""
简单脚本，检查Fashion Agent相关组件是否正常工作
这个脚本测试模型加载、图像分析和文本处理功能
"""
import os
import sys
import argparse

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试Fashion Agent组件")
    parser.add_argument("--test-web", action="store_true", help="测试Web界面")
    args = parser.parse_args()
    
    print("🔍 开始测试Fashion Agent组件...")
    
    # 添加必要的路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_root)
    
    # 测试Ollama连接
    print("\n📡 测试Ollama连接...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print("✅ Ollama服务可用")
            
            # 检查模型
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            
            print(f"发现的模型: {', '.join(model_names) if model_names else '无'}")
        else:
            print(f"❌ Ollama服务响应异常: {response.status_code}")
    except Exception as e:
        print(f"❌ 无法连接到Ollama服务: {e}")
        print("请确保已安装Ollama并运行 'ollama serve' 命令")
        return
    
    # 测试配置文件加载
    print("\n📄 测试配置文件加载...")
    try:
        import yaml
        with open("config.yaml", 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("✅ 配置文件加载成功")
    except Exception as e:
        print(f"❌ 配置文件加载失败: {e}")
        return
    
    # 测试模型导入
    print("\n📦 测试模型导入...")
    try:
        from models.text_agent import TextAgent
        from models.image import ImageModel
        print("✅ 模型类导入成功")
    except Exception as e:
        print(f"❌ 模型导入失败: {e}")
        return
    
    # 测试代理导入
    print("\n🤖 测试代理导入...")
    try:
        from agents.fashion_agent import FashionAgent
        print("✅ Fashion Agent导入成功")
    except Exception as e:
        print(f"❌ Fashion Agent导入失败: {e}")
        return
    
    # 测试代理初始化
    print("\n🚀 测试代理初始化...")
    try:
        agent = FashionAgent()
        print("✅ Fashion Agent初始化成功")
    except Exception as e:
        print(f"❌ Fashion Agent初始化失败: {e}")
        return
    
    # 测试Web界面
    if args.test_web:
        print("\n🌐 测试Web界面...")
        try:
            import gradio as gr
            from web.app import demo
            print("✅ Web界面导入成功")
            
            print("启动Web界面进行测试（按Ctrl+C终止）...")
            demo.launch(share=False, debug=True)
        except Exception as e:
            print(f"❌ Web界面测试失败: {e}")
            return
    
    print("\n✨ 所有测试完成!")

if __name__ == "__main__":
    main()
