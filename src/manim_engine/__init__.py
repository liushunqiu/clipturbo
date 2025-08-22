"""
Manim Engine Module for ClipTurbo

This module provides the core Manim-based video rendering engine,
including template system, scene management, and rendering pipeline.
"""

from .template_system import TemplateManager, VideoTemplate, TemplateParameter
from .render_manager import RenderManager, RenderConfig, RenderResult, RenderQuality

__all__ = [
    'TemplateManager',
    'VideoTemplate', 
    'TemplateParameter',
    'RenderManager',
    'RenderConfig',
    'RenderResult',
    'RenderQuality'
]
