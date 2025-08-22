#!/usr/bin/env python3
"""
ClipTurbo 用户文案输入示例
演示如何使用用户提供的文案生成视频，跳过AI文案生成步骤
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8000/api"

async def generate_video_with_user_content():
    """使用用户提供的文案生成视频"""
    
    # 用户提供的完整文案内容
    user_content = {
        "title": "如何提高工作效率",
        "script": """
        大家好，今天分享5个提高工作效率的小技巧：
        
        1. 使用番茄工作法，25分钟专注工作，5分钟休息
        2. 制定每日任务清单，按优先级排序
        3. 减少不必要的会议和打断
        4. 学会说"不"，专注重要任务
        5. 定期整理工作环境，保持桌面整洁
        
        这些方法简单易行，坚持使用会显著提升你的工作效率！
        """,
        "language": "zh-CN",
        "style": "professional",
        "duration": 45
    }
    
    # 生成要求
    requirements = {
        "template_style": "simple_text",
        "background_color": "#f0f0f0",
        "text_color": "#333333",
        "font_size": 24,
        "animation_speed": "medium"
    }
    
    # 构建请求数据
    request_data = {
        "content": user_content,
        "requirements": requirements
    }
    
    async with aiohttp.ClientSession() as session:
        # 发起视频生成请求
        async with session.post(
            f"{BASE_URL}/generate/with-content",
            json=request_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                workflow_id = result["workflow_id"]
                print(f"✅ 视频生成任务已启动，工作流ID: {workflow_id}")
                
                # 监控工作流状态
                await monitor_workflow(session, workflow_id)
            else:
                error = await response.text()
                print(f"❌ 请求失败: {error}")

async def generate_video_with_mixed_mode():
    """使用通用接口的混合模式示例"""
    
    # 方式1: 使用AI生成模式（传入topic）
    ai_request = {
        "topic": "健康饮食的重要性",
        "requirements": {
            "language": "zh-CN",
            "style": "educational",
            "duration": 60
        }
    }
    
    # 方式2: 使用用户内容模式（传入content）
    content_request = {
        "content": {
            "title": "早起的好处",
            "script": "早起能让你拥有更多时间规划一天，提高工作效率，改善身体健康...",
            "language": "zh-CN",
            "duration": 30
        },
        "requirements": {
            "template_style": "motivational"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        # 使用用户内容模式
        print("🎬 使用用户内容模式生成视频...")
        async with session.post(f"{BASE_URL}/generate", json=content_request) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ 用户内容模式启动成功: {result['workflow_id']}")
            else:
                print(f"❌ 用户内容模式失败: {await response.text()}")

async def monitor_workflow(session: aiohttp.ClientSession, workflow_id: str):
    """监控工作流执行状态"""
    print(f"\n📊 监控工作流状态: {workflow_id}")
    
    while True:
        async with session.get(f"{BASE_URL}/workflows/{workflow_id}") as response:
            if response.status == 200:
                status = await response.json()
                print(f"状态: {status['status']}")
                
                # 显示步骤进度
                for step_name, step_info in status.get('steps', {}).items():
                    step_status = step_info.get('status', 'unknown')
                    print(f"  - {step_name}: {step_status}")
                
                # 检查是否完成
                if status['status'] in ['COMPLETED', 'FAILED']:
                    if status['status'] == 'COMPLETED':
                        print(f"🎉 视频生成完成！")
                        if 'output_path' in status:
                            print(f"📁 输出文件: {status['output_path']}")
                    else:
                        print(f"💥 视频生成失败: {status.get('error', '未知错误')}")
                    break
                
                # 等待5秒后再次检查
                await asyncio.sleep(5)
            else:
                print(f"❌ 获取状态失败: {await response.text()}")
                break

async def main():
    """主函数"""
    print("🚀 ClipTurbo 用户文案输入示例")
    print("=" * 50)
    
    try:
        # 示例1: 使用专用接口
        print("\n📝 示例1: 使用用户提供的完整文案")
        await generate_video_with_user_content()
        
        print("\n" + "=" * 50)
        
        # 示例2: 使用通用接口
        print("\n🔄 示例2: 使用通用接口的混合模式")
        await generate_video_with_mixed_mode()
        
    except Exception as e:
        print(f"❌ 执行出错: {str(e)}")

if __name__ == "__main__":
    # 运行示例
    asyncio.run(main())
