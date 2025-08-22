#!/usr/bin/env python3
"""
测试ModelScope翻译服务
"""

import asyncio
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai_services.translation_service import ModelScopeTranslateProvider, TranslationService

async def test_modelscope_provider():
    """测试ModelScope翻译提供者"""
    
    # 使用配置的SDK Token
    sdk_token = "ms-c0d318a3-9811-4fac-8f4a-353383a30edd"
    
    provider = ModelScopeTranslateProvider(sdk_token)
    
    # 测试英译中
    test_texts = [
        "Hello, world!",
        "Alibaba Group's mission is to let the world have no difficult business",
        "Machine learning is a subset of artificial intelligence.",
        "The weather is nice today."
    ]
    
    print("🧪 测试ModelScope英译中功能:")
    print("=" * 50)
    
    for text in test_texts:
        try:
            print(f"\n原文 (EN): {text}")
            translated = await provider.translate(text, "en", "zh-CN")
            print(f"译文 (ZH): {translated}")
            print("✅ 翻译成功")
        except Exception as e:
            print(f"❌ 翻译失败: {str(e)}")

async def test_translation_service():
    """测试翻译服务管理器"""
    
    config = {
        'cache_enabled': True
    }
    
    service = TranslationService(config)
    
    print("\n🔧 测试翻译服务管理器:")
    print("=" * 50)
    
    # 检查服务状态
    print(f"服务可用性: {service.is_available()}")
    print(f"提供者状态: {service.get_provider_status()}")
    
    # 测试翻译
    test_text = "Hello, how are you today?"
    try:
        result = await service.translate(test_text, "en", "zh-CN")
        print(f"\n原文: {test_text}")
        print(f"译文: {result}")
        print("✅ 服务翻译成功")
    except Exception as e:
        print(f"❌ 服务翻译失败: {str(e)}")

def test_direct_api():
    """直接测试ModelScope API调用"""
    import json
    import requests
    
    # 使用你提供的API示例
    API_URL = "https://api-inference.modelscope.cn/api-inference/v1/models/iic/nlp_csanmt_translation_en2zh"
    
    # 使用配置的SDK Token
    sdk_token = "ms-c0d318a3-9811-4fac-8f4a-353383a30edd"
    
    headers = {"Authorization": f"Bearer {sdk_token}"}
    
    def query(payload):
        data = json.dumps(payload)
        response = requests.post(API_URL, headers=headers, data=data)
        return json.loads(response.content.decode("utf-8"))
    
    print("\n🌐 直接测试ModelScope API:")
    print("=" * 50)
    
    payload = {"input": "Alibaba Group's mission is to let the world have no difficult business"}
    
    try:
        output = query(payload)
        print(f"请求: {payload}")
        print(f"响应: {output}")
        print("✅ API调用成功")
    except Exception as e:
        print(f"❌ API调用失败: {str(e)}")

async def main():
    """主测试函数"""
    print("🚀 ModelScope翻译服务测试")
    print("=" * 60)
    
    # 测试1: 直接API调用
    test_direct_api()
    
    # 测试2: ModelScope提供者
    await test_modelscope_provider()
    
    # 测试3: 翻译服务管理器
    await test_translation_service()
    
    print("\n" + "=" * 60)
    print("📝 使用说明:")
    print("1. ModelScope SDK Token已配置: ms-c0d318a3-9811-4fac-8f4a-353383a30edd")
    print("2. 翻译服务已简化，仅支持英译中")
    print("3. 无需额外配置，开箱即用")

if __name__ == "__main__":
    asyncio.run(main())
