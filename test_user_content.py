#!/usr/bin/env python3
"""
测试用户文案输入功能
"""

import asyncio
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.workflow_engine import WorkflowEngine
from ai_services.ai_orchestrator import AIOrchestrator
from manim_engine.template_system import TemplateManager
from manim_engine.render_manager import RenderManager

async def test_user_content_workflow():
    """测试用户内容工作流"""
    
    # 创建模拟的依赖对象
    ai_orchestrator = AIOrchestrator()
    template_manager = TemplateManager()
    render_manager = RenderManager()
    
    # 创建工作流引擎
    workflow_engine = WorkflowEngine(ai_orchestrator, template_manager, render_manager)
    
    # 测试数据：用户提供的完整文案
    user_content = {
        "title": "测试视频",
        "script": "这是一个测试文案，用来验证用户直接提供内容的功能。",
        "language": "zh-CN",
        "style": "simple",
        "duration": 30
    }
    
    requirements = {
        "template_style": "simple_text",
        "output_format": "mp4"
    }
    
    try:
        print("🧪 开始测试用户内容工作流...")
        
        # 创建工作流
        workflow_id = await workflow_engine.create_video_workflow(
            content_input=user_content,
            requirements=requirements
        )
        
        print(f"✅ 工作流创建成功: {workflow_id}")
        
        # 获取工作流状态
        workflow_status = workflow_engine.get_workflow_status(workflow_id)
        print(f"📊 工作流状态: {workflow_status.status}")
        
        # 检查步骤配置
        steps = workflow_status.steps
        expected_steps = ['content_preparation', 'template_selection', 'parameter_preparation', 'scene_creation', 'video_rendering', 'post_processing']
        
        print("🔍 检查工作流步骤:")
        for step_name in expected_steps:
            if step_name in steps:
                print(f"  ✅ {step_name}: 已配置")
            else:
                print(f"  ❌ {step_name}: 缺失")
        
        # 验证不包含AI生成步骤
        if 'content_generation' not in steps:
            print("  ✅ content_generation: 正确跳过")
        else:
            print("  ❌ content_generation: 不应该包含")
        
        print("🎉 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

async def test_ai_content_workflow():
    """测试AI内容工作流（对比测试）"""
    
    # 创建模拟的依赖对象
    ai_orchestrator = AIOrchestrator()
    template_manager = TemplateManager()
    render_manager = RenderManager()
    
    # 创建工作流引擎
    workflow_engine = WorkflowEngine(ai_orchestrator, template_manager, render_manager)
    
    # 测试数据：AI生成模式
    topic = "如何学习编程"
    requirements = {
        "language": "zh-CN",
        "style": "educational",
        "duration": 60
    }
    
    try:
        print("🤖 开始测试AI内容工作流...")
        
        # 创建工作流
        workflow_id = await workflow_engine.create_video_workflow(
            content_input=topic,
            requirements=requirements
        )
        
        print(f"✅ 工作流创建成功: {workflow_id}")
        
        # 获取工作流状态
        workflow_status = workflow_engine.get_workflow_status(workflow_id)
        print(f"📊 工作流状态: {workflow_status.status}")
        
        # 检查步骤配置
        steps = workflow_status.steps
        expected_steps = ['content_generation', 'template_selection', 'parameter_preparation', 'scene_creation', 'video_rendering', 'post_processing']
        
        print("🔍 检查工作流步骤:")
        for step_name in expected_steps:
            if step_name in steps:
                print(f"  ✅ {step_name}: 已配置")
            else:
                print(f"  ❌ {step_name}: 缺失")
        
        # 验证不包含用户内容准备步骤
        if 'content_preparation' not in steps:
            print("  ✅ content_preparation: 正确跳过")
        else:
            print("  ❌ content_preparation: 不应该包含")
        
        print("🎉 测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """主测试函数"""
    print("🚀 ClipTurbo 工作流测试")
    print("=" * 50)
    
    # 测试用户内容模式
    await test_user_content_workflow()
    
    print("\n" + "=" * 50)
    
    # 测试AI内容模式
    await test_ai_content_workflow()

if __name__ == "__main__":
    asyncio.run(main())
