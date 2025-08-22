#!/usr/bin/env python3
"""
双语字幕视频生成示例
演示如何使用双语字幕模板创建类似短视频平台的双语内容
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any

# API基础URL
BASE_URL = "http://localhost:8000/api"

async def create_bilingual_video():
    """创建双语字幕视频"""
    
    # 用户提供的中文文案
    user_content = {
        "title": "亲子关系的智慧",
        "script": """
        别总盯着孩子，先过好你自己的日子。
        是不是又在守着电话，等孩子那半个月才来一次的问候？
        一接通，三句话问不出个所以然，就把电话给挂了。
        然后自己在这边生半天气，觉得养了个白眼狼？
        """,
        "language": "zh-CN",
        "style": "emotional",
        "duration": 15  # 每段3-4秒，总共约15秒
    }
    
    # 双语字幕模板配置
    requirements = {
        "template_style": "bilingual_subtitle",
        "background_color": "#000000",  # 黑色背景
        "chinese_font_size": 48,
        "english_font_size": 36,
        "segment_duration": 3.5,  # 每段显示3.5秒
        "show_emoji": True,
        "highlight_style": "glow",
        "video_format": "mp4",
        "resolution": "1080x1920",  # 竖屏格式
        "fps": 30
    }
    
    # 构建请求数据
    request_data = {
        "content": user_content,
        "requirements": requirements
    }
    
    async with aiohttp.ClientSession() as session:
        try:
            # 发起视频生成请求
            async with session.post(
                f"{BASE_URL}/generate/with-content",
                json=request_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    workflow_id = result["workflow_id"]
                    print(f"✅ 双语字幕视频生成任务已启动")
                    print(f"🆔 工作流ID: {workflow_id}")
                    
                    # 监控工作流状态
                    await monitor_workflow(session, workflow_id)
                else:
                    error = await response.text()
                    print(f"❌ 请求失败: {error}")
                    
        except Exception as e:
            print(f"❌ 连接失败: {str(e)}")
            print("请确保ClipTurbo服务正在运行 (python main.py)")

async def create_educational_video():
    """创建教育类双语视频"""
    
    user_content = {
        "title": "学习方法分享",
        "script": """
        学习不是死记硬背，而是要理解原理。
        每天花30分钟复习，比临时抱佛脚效果好100倍。
        做笔记的时候，用自己的话总结，不要照抄。
        遇到不懂的问题，立刻问老师或同学，不要拖延。
        """,
        "language": "zh-CN",
        "style": "educational",
        "duration": 16
    }
    
    requirements = {
        "template_style": "bilingual_subtitle",
        "background_color": "#1a1a2e",  # 深蓝色背景
        "chinese_font_size": 44,
        "english_font_size": 32,
        "segment_duration": 4.0,
        "show_emoji": True,
        "highlight_style": "background",
        "video_format": "mp4"
    }
    
    request_data = {
        "content": user_content,
        "requirements": requirements
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/generate/with-content",
            json=request_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                print(f"✅ 教育类双语视频生成任务已启动: {result['workflow_id']}")
            else:
                print(f"❌ 教育视频生成失败: {await response.text()}")

async def monitor_workflow(session: aiohttp.ClientSession, workflow_id: str):
    """监控工作流执行状态"""
    print(f"\n📊 监控双语视频生成进度...")
    print("=" * 50)
    
    step_descriptions = {
        'content_preparation': '📝 准备双语内容',
        'template_selection': '🎨 选择视频模板',
        'parameter_preparation': '⚙️ 配置模板参数',
        'scene_creation': '🎬 创建视频场景',
        'video_rendering': '🎥 渲染视频文件',
        'post_processing': '✨ 后期处理'
    }
    
    while True:
        try:
            async with session.get(f"{BASE_URL}/workflows/{workflow_id}") as response:
                if response.status == 200:
                    status = await response.json()
                    current_status = status['status']
                    
                    print(f"\r🔄 整体状态: {current_status}", end="")
                    
                    # 显示详细步骤进度
                    for step_name, step_info in status.get('steps', {}).items():
                        step_status = step_info.get('status', 'pending')
                        description = step_descriptions.get(step_name, step_name)
                        
                        if step_status == 'completed':
                            print(f"\n✅ {description}")
                        elif step_status == 'running':
                            print(f"\n🔄 {description} (进行中...)")
                        elif step_status == 'failed':
                            error = step_info.get('error', '未知错误')
                            print(f"\n❌ {description} - 失败: {error}")
                    
                    # 检查是否完成
                    if current_status == 'COMPLETED':
                        print(f"\n\n🎉 双语字幕视频生成完成！")
                        if 'output_path' in status:
                            print(f"📁 输出文件: {status['output_path']}")
                        print(f"⏱️  总耗时: {status.get('total_duration', 0):.1f}秒")
                        break
                    elif current_status == 'FAILED':
                        print(f"\n\n💥 视频生成失败: {status.get('error', '未知错误')}")
                        break
                    
                    # 等待3秒后再次检查
                    await asyncio.sleep(3)
                else:
                    print(f"\n❌ 获取状态失败: {await response.text()}")
                    break
                    
        except Exception as e:
            print(f"\n❌ 监控出错: {str(e)}")
            break

async def test_template_parameters():
    """测试不同的模板参数"""
    
    print("🧪 测试不同的双语字幕样式...")
    
    base_content = {
        "title": "参数测试",
        "script": "这是一个测试文案，用来验证不同的视觉效果。",
        "language": "zh-CN"
    }
    
    # 测试不同的高亮样式
    highlight_styles = ["glow", "underline", "background", "scale"]
    
    for style in highlight_styles:
        print(f"\n🎨 测试高亮样式: {style}")
        
        requirements = {
            "template_style": "bilingual_subtitle",
            "highlight_style": style,
            "segment_duration": 2.0,
            "background_color": "#000000" if style != "background" else "#1a1a2e"
        }
        
        request_data = {
            "content": base_content,
            "requirements": requirements
        }
        
        # 这里可以发送请求测试不同样式
        print(f"   配置: {json.dumps(requirements, indent=2, ensure_ascii=False)}")

async def main():
    """主函数"""
    print("🚀 ClipTurbo 双语字幕视频生成示例")
    print("=" * 60)
    
    try:
        # 示例1: 情感类双语视频
        print("\n📱 示例1: 创建情感类双语字幕视频")
        await create_bilingual_video()
        
        print("\n" + "=" * 60)
        
        # 示例2: 教育类双语视频
        print("\n📚 示例2: 创建教育类双语字幕视频")
        await create_educational_video()
        
        print("\n" + "=" * 60)
        
        # 示例3: 参数测试
        print("\n⚙️ 示例3: 测试模板参数")
        await test_template_parameters()
        
    except Exception as e:
        print(f"❌ 执行出错: {str(e)}")

if __name__ == "__main__":
    print("📋 功能特性:")
    print("• 🌐 自动英中互译")
    print("• 😊 智能表情匹配") 
    print("• 🎨 多种高亮样式")
    print("• 📱 竖屏短视频格式")
    print("• ⚡ 实时进度监控")
    print()
    
    # 运行示例
    asyncio.run(main())
