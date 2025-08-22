#!/usr/bin/env python3
"""
简单的Manim场景测试
"""

from manim import Scene, Text, Write, Create, Circle, VGroup, BLUE, UP

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

if __name__ == "__main__":
    from manim import config
    config.pixel_width = 854
    config.pixel_height = 480
    config.frame_rate = 30
    
    scene = SimpleTestScene()
    scene.render()