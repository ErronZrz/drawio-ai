#!/usr/bin/env python3
"""
GLM API 连接测试脚本
用于验证 API_KEY 是否有效

使用 OpenAI 兼容接口格式调用智谱 API
Base URL: https://open.bigmodel.cn/api/coding/paas/v4
"""
import os
import sys
import ssl
import warnings

# 禁用 SSL 验证警告（本地开发环境使用 Whistle 代理）
warnings.filterwarnings('ignore', message='Unverified HTTPS request')

# 禁用 SSL 验证（解决 Whistle 代理证书问题）
SSL_VERIFY = False

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 智谱 OpenAI 兼容接口地址
GLM_BASE_URL = "https://open.bigmodel.cn/api/coding/paas/v4"


def test_glm_connection():
    """测试 GLM API 连接（使用 OpenAI 兼容格式）"""
    api_key = os.getenv("GLM_API_KEY", "")
    model = os.getenv("GLM_MODEL", "GLM-4.7")
    
    print("=" * 50)
    print("GLM API 连接测试 (OpenAI 兼容模式)")
    print("=" * 50)
    
    # 检查 API Key 是否配置
    if not api_key:
        print("❌ 错误: GLM_API_KEY 未配置")
        print("   请在 .env 文件中设置 GLM_API_KEY")
        return False
    
    if api_key == "your_glm_api_key_here":
        print("❌ 错误: GLM_API_KEY 是默认占位值")
        print("   请在 .env 文件中设置真实的 API Key")
        return False
    
    print(f"✓ API Key 已配置 (前8位: {api_key[:8]}...)")
    print(f"✓ 使用模型: {model}")
    print(f"✓ Base URL: {GLM_BASE_URL}")
    print()
    
    # 尝试导入 openai
    try:
        from openai import OpenAI
        print("✓ openai 库已安装")
    except ImportError:
        print("❌ 错误: openai 库未安装")
        print("   请运行: pip install openai")
        return False
    
    # 尝试导入 httpx (用于自定义 http client)
    try:
        import httpx
    except ImportError:
        print("⚠️ httpx 库未安装，使用默认配置")
        httpx = None
    
    # 先测试网络连通性
    print()
    print("正在测试网络连通性...")
    print("-" * 50)
    
    try:
        import requests
        # 测试能否访问智谱域名，禁用 SSL 验证
        test_url = "https://open.bigmodel.cn"
        resp = requests.get(test_url, timeout=10, verify=SSL_VERIFY)
        print(f"✓ 网络连通: {test_url} (状态码: {resp.status_code})")
        if not SSL_VERIFY:
            print("  (注意: SSL 验证已禁用，仅用于本地开发环境)")
    except ImportError:
        print("⚠️ requests 库未安装，跳过网络测试")
    except Exception as net_err:
        print(f"❌ 网络测试失败: {net_err}")
        print("   请检查网络连接或代理设置")
    
    # 测试 API 调用
    print()
    print("正在测试 API 连接...")
    print("-" * 50)
    
    try:
        # 使用 OpenAI 兼容格式，增加超时设置，禁用 SSL 验证
        import httpx
        http_client = httpx.Client(timeout=60.0, verify=SSL_VERIFY)
        client = OpenAI(
            api_key=api_key,
            base_url=GLM_BASE_URL,
            http_client=http_client
        )
        
        # 构建消息列表
        user_message = {
            "role": "user",
            "content": "你好，请用一句话介绍你自己。"
        }
        
        response = client.chat.completions.create(
            model=model,
            messages=[user_message],  # type: ignore
            max_tokens=100
        )
        
        reply = response.choices[0].message.content or ""
        
        print("✓ API 调用成功!")
        print()
        if reply.strip():
            print("GLM 回复:")
            print(f"  {reply}")
        else:
            print("GLM 回复: (空)")
            print("  注意: 智谱 Coding API 主要用于代码生成，普通对话可能返回空内容")
            print("  这不影响图表生成功能的使用")
        print()
        print("=" * 50)
        print("✅ 测试通过! API Key 有效，可以正常使用。")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"❌ API 调用失败: {str(e)}")
        print()
        print("可能的原因:")
        print("  1. API Key 无效或已过期")
        print("  2. 网络连接问题")
        print("  3. API 配额已用完")
        print("  4. 模型名称不正确")
        return False


def test_simple_diagram_generation():
    """测试简单的图表生成"""
    api_key = os.getenv("GLM_API_KEY", "")
    model = os.getenv("GLM_MODEL", "GLM-4.7")
    
    if not api_key or api_key == "your_glm_api_key_here":
        print("跳过图表生成测试 (API Key 未配置)")
        return False
    
    print()
    print("=" * 50)
    print("图表生成测试")
    print("=" * 50)
    print()
    print("正在测试图表生成能力...")
    print("-" * 50)
    
    try:
        from openai import OpenAI
        import httpx
        http_client = httpx.Client(timeout=60.0, verify=SSL_VERIFY)
        client = OpenAI(
            api_key=api_key,
            base_url=GLM_BASE_URL,
            http_client=http_client
        )
        
        test_prompt = """请生成一个简单的draw.io流程图XML，包含三个节点：开始、处理、结束，用箭头连接。

直接输出XML代码："""

        # 构建消息
        user_message = {"role": "user", "content": test_prompt}
        
        response = client.chat.completions.create(
            model=model,
            messages=[user_message],  # type: ignore
            max_tokens=2000,
            temperature=0.7
        )
        
        reply = response.choices[0].message.content or ""
        
        # 检查响应是否为空
        if not reply.strip():
            print("⚠️ 响应为空，模型未返回内容")
            print("   这可能是因为模型拒绝生成或请求被过滤")
            return False
        
        # 检查是否包含 mxGraphModel 或其他图表标识
        if "mxGraphModel" in reply or "mxCell" in reply or "<diagram" in reply:
            print("✓ 图表生成成功!")
            print()
            print("生成的 XML (前500字符):")
            print("-" * 30)
            print(reply[:500] + ("..." if len(reply) > 500 else ""))
            print("-" * 30)
            print()
            print("✅ 图表生成测试通过!")
            return True
        else:
            print("⚠️ 响应可能不包含有效的图表 XML")
            print(f"响应内容: {reply[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ 图表生成测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    print()
    
    # 测试 API 连接
    connection_ok = test_glm_connection()
    
    if connection_ok:
        # 测试图表生成
        test_simple_diagram_generation()
    
    print()
