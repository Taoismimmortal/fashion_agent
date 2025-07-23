"""
启动脚本 - 运行AI时尚搭配助手
"""
import os
import sys
import argparse

def check_ollama():
    """检查Ollama服务是否可用"""
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print("✅ Ollama服务已运行")
            
            # 检查所需模型
            models = response.json().get("models", [])
            model_names = [model.get("name") for model in models]
            
            if "minicpm-v:8b-2.6" in model_names or "minicpm-v:8b-2.6-q4_K_M" in model_names:
                print("✅ MiniCPM-V 模型已可用")
            else:
                print("⚠️ MiniCPM-V 模型未找到，首次使用时将自动下载")
            
            if any(name.startswith("qwen") for name in model_names):
                print("✅ Qwen 模型已可用")
            else:
                print("⚠️ Qwen 模型未找到，首次使用时将自动下载")
                
            return True
        else:
            print(f"❌ Ollama服务响应异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法连接到Ollama服务: {e}")
        print("请确保已安装Ollama并运行 'ollama serve' 命令")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AI时尚搭配助手")
    parser.add_argument("--debug", action="store_true", help="启用调试模式")
    parser.add_argument("--port", type=int, default=7860, help="Web服务端口")
    parser.add_argument("--share", action="store_true", help="创建公共链接分享应用")
    args = parser.parse_args()
    


    
    # 检查Ollama
    if not check_ollama() and not args.debug:
        print("是否仍要继续启动? [y/N]", end=" ")
        choice = input().strip().lower()
        if choice != 'y':
            print("启动已取消")
            sys.exit(1)
    
    print("\n🚀 启动AI时尚搭配助手...")
    
    # 添加必要的路径
    project_root = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(project_root)
    
    # 导入web应用
    from web.app import demo
    
    # 启动web服务
    demo.launch(
        server_name="0.0.0.0" if args.share else "127.0.0.1",
        server_port=args.port,
        share=args.share,
        debug=args.debug
    )

if __name__ == "__main__":
    main()
