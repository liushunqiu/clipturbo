#!/usr/bin/env python3
"""
Manim渲染测试场景
"""

from manim import Scene, Text, Write, Create, Circle, VGroup, BLUE

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