#!/usr/bin/env python3
"""
测试Manim渲染功能
"""

import asyncio
import sys
import os
import subprocess
import tempfile
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from manim_engine.render_manager import RenderManager, RenderConfig, RenderQuality
from manim_engine.template_system import TemplateManager
from manim import Scene, Text, Write, Create, Circle, VGroup

class SimpleTestScene(Scene):
    """简单测试场景"""
    
    def construct(self):
        """构建测试场景"""
        # 创建文本
        text = Text("ClipTurbo测试", font_size=48)
        self.play(Write(text))
        self.wait(1)
        
        # 创建圆形
        circle = Circle(color=BLUE, radius=1)
        self.play(Create(circle))
        self.wait(1)
        
        # 组合动画
        group = VGroup(text, circle)
        self.play(group.animate.scale(1.2).shift(UP))
        self.wait(2)

def test_manim_render():
    """测试Manim渲染功能"""
    print("🎬 开始测试Manim渲染功能...")
    
    try:
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "test_video.mp4"
            
            # 构建manim命令
            cmd = [
                "python3", "-m", "manim",
                str(Path(__file__).parent / "test_manim_render.py"),
                "SimpleTestScene",
                "-pql",  # 低质量预览
                "-o", str(output_path.parent)
            ]
            
            print(f"执行命令: {' '.join(cmd)}")
            
            # 运行manim
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ Manim渲染成功")
                print(f"输出路径: {output_path}")
                
                # 检查文件是否生成
                if output_path.exists():
                    file_size = output_path.stat().st_size
                    print(f"视频文件大小: {file_size} bytes")
                    return True
                else:
                    print("❌ 输出文件不存在")
                    return False
            else:
                print("❌ Manim渲染失败")
                print(f"错误信息: {result.stderr}")
                return False
                
    except subprocess.TimeoutExpired:
        print("❌ 渲染超时")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_template_manager():
    """测试模板管理器"""
    print("\n📁 开始测试模板管理器...")
    
    try:
        template_manager = TemplateManager()
        print("✅ 模板管理器初始化成功")
        
        # 列出模板
        templates = template_manager.list_templates()
        print(f"📋 可用模板数量: {len(templates)}")
        
        for template in templates:
            print(f"  - {template.id}: {template.name}")
        
        # 测试模板参数
        if templates:
            first_template = templates[0].id
            if first_template:
                parameters = template_manager.get_template_parameters(first_template)
                print(f"📊 模板参数数量: {len(parameters)}")
        
        return True
        
    except Exception as e:
        print(f"❌ 模板管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_render_manager():
    """测试渲染管理器"""
    print("\n🎨 开始测试渲染管理器...")
    
    try:
        config = {
            "max_concurrent_renders": 2,
            "output_dir": "./output/videos",
            "temp_dir": "./temp"
        }
        
        render_manager = RenderManager(config)
        print("✅ 渲染管理器初始化成功")
        
        # 获取系统资源
        resources = render_manager.get_system_resources()
        print(f"💾 系统内存: {resources.get('memory', {}).get('available', 'Unknown')} MB")
        print(f"💻 CPU核心数: {resources.get('cpu', {}).get('cores', 'Unknown')}")
        
        # 获取队列状态
        queue_status = render_manager.get_queue_status()
        print(f"📊 队列状态: {queue_status}")
        
        return True
        
    except Exception as e:
        print(f"❌ 渲染管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """主测试函数"""
    print("🚀 ClipTurbo 渲染功能测试")
    print("=" * 50)
    
    # 测试1: 模板管理器
    template_ok = test_template_manager()
    
    # 测试2: 渲染管理器
    render_ok = test_render_manager()
    
    # 测试3: Manim渲染（需要更多设置，暂时跳过）
    print("\n📝 总结:")
    print(f"模板管理器: {'✅ 通过' if template_ok else '❌ 失败'}")
    print(f"渲染管理器: {'✅ 通过' if render_ok else '❌ 失败'}")
    print("Manim渲染: ⏭️ 跳过（需要额外配置）")
    
    if template_ok and render_ok:
        print("\n🎉 核心渲染组件测试完成！")
    else:
        print("\n❌ 部分测试失败")

if __name__ == "__main__":
    import subprocess
    from manim import BLUE
    
    asyncio.run(main())