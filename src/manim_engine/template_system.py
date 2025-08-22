"""
Template System - Manim模板管理系统
"""

import json
import inspect
from typing import Dict, Any, List, Optional, Type, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from pathlib import Path
from enum import Enum
import logging

from manim import Scene, Text, Rectangle, Circle, VGroup, Animation
from manim import FadeIn, FadeOut, Write, Transform, Create


class ParameterType(Enum):
    """参数类型枚举"""
    TEXT = "text"
    NUMBER = "number"
    COLOR = "color"
    FONT = "font"
    IMAGE = "image"
    AUDIO = "audio"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    DURATION = "duration"


@dataclass
class TemplateParameter:
    """模板参数定义"""
    name: str
    type: ParameterType
    description: str
    default_value: Any = None
    required: bool = True
    choices: Optional[List[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    validation_pattern: Optional[str] = None


@dataclass
class TemplateMetadata:
    """模板元数据"""
    id: str
    name: str
    description: str
    category: str
    author: str
    version: str
    tags: List[str] = field(default_factory=list)
    preview_image: Optional[str] = None
    duration_range: tuple = (10, 120)  # 支持的时长范围(秒)
    aspect_ratios: List[str] = field(default_factory=lambda: ["16:9", "9:16", "1:1"])
    difficulty: str = "beginner"  # beginner, intermediate, advanced


class VideoTemplate(ABC):
    """视频模板抽象基类"""
    
    def __init__(self):
        self.metadata = self.get_metadata()
        self.parameters = self.get_parameters()
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def get_metadata(self) -> TemplateMetadata:
        """获取模板元数据"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[TemplateParameter]:
        """获取模板参数定义"""
        pass
    
    @abstractmethod
    def create_scene(self, params: Dict[str, Any]) -> Type[Scene]:
        """创建Manim场景类"""
        pass
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """验证和处理参数"""
        validated_params = {}
        
        for param in self.parameters:
            value = params.get(param.name, param.default_value)
            
            # 检查必需参数
            if param.required and value is None:
                raise ValueError(f"参数 '{param.name}' 是必需的")
            
            # 类型验证和转换
            if value is not None:
                validated_value = self._validate_parameter_value(param, value)
                validated_params[param.name] = validated_value
        
        return validated_params
    
    def _validate_parameter_value(self, param: TemplateParameter, value: Any) -> Any:
        """验证单个参数值"""
        if param.type == ParameterType.TEXT:
            return str(value)
        elif param.type == ParameterType.NUMBER:
            num_value = float(value)
            if param.min_value is not None and num_value < param.min_value:
                raise ValueError(f"参数 '{param.name}' 值 {num_value} 小于最小值 {param.min_value}")
            if param.max_value is not None and num_value > param.max_value:
                raise ValueError(f"参数 '{param.name}' 值 {num_value} 大于最大值 {param.max_value}")
            return num_value
        elif param.type == ParameterType.BOOLEAN:
            return bool(value)
        elif param.type == ParameterType.CHOICE:
            if param.choices and value not in param.choices:
                raise ValueError(f"参数 '{param.name}' 值 '{value}' 不在允许的选择中: {param.choices}")
            return value
        elif param.type == ParameterType.COLOR:
            # 简单的颜色验证
            if isinstance(value, str) and (value.startswith('#') or value.lower() in ['red', 'blue', 'green', 'white', 'black']):
                return value
            raise ValueError(f"无效的颜色值: {value}")
        else:
            return value


class SimpleTextTemplate(VideoTemplate):
    """简单文本模板"""
    
    def get_metadata(self) -> TemplateMetadata:
        return TemplateMetadata(
            id="simple_text",
            name="简单文本",
            description="基础的文本展示模板，适合标题和简短内容",
            category="text",
            author="ClipTurbo",
            version="1.0.0",
            tags=["text", "simple", "basic"],
            duration_range=(5, 30)
        )
    
    def get_parameters(self) -> List[TemplateParameter]:
        return [
            TemplateParameter(
                name="title",
                type=ParameterType.TEXT,
                description="主标题文本",
                required=True
            ),
            TemplateParameter(
                name="subtitle",
                type=ParameterType.TEXT,
                description="副标题文本",
                default_value="",
                required=False
            ),
            TemplateParameter(
                name="font_size",
                type=ParameterType.NUMBER,
                description="字体大小",
                default_value=48,
                min_value=12,
                max_value=120
            ),
            TemplateParameter(
                name="text_color",
                type=ParameterType.COLOR,
                description="文字颜色",
                default_value="WHITE"
            ),
            TemplateParameter(
                name="background_color",
                type=ParameterType.COLOR,
                description="背景颜色",
                default_value="BLACK"
            ),
            TemplateParameter(
                name="animation_style",
                type=ParameterType.CHOICE,
                description="动画风格",
                default_value="fade",
                choices=["fade", "write", "slide"]
            )
        ]
    
    def create_scene(self, params: Dict[str, Any]) -> Type[Scene]:
        """创建简单文本场景"""
        validated_params = self.validate_parameters(params)
        
        class SimpleTextScene(Scene):
            def construct(self):
                # 设置背景
                self.camera.background_color = validated_params['background_color']
                
                # 创建标题
                title = Text(
                    validated_params['title'],
                    font_size=validated_params['font_size'],
                    color=validated_params['text_color']
                )
                
                # 创建副标题
                subtitle_text = validated_params.get('subtitle', '')
                if subtitle_text:
                    subtitle = Text(
                        subtitle_text,
                        font_size=validated_params['font_size'] * 0.6,
                        color=validated_params['text_color']
                    )
                    subtitle.next_to(title, direction=DOWN, buff=0.5)
                    
                    # 组合文本
                    text_group = VGroup(title, subtitle)
                else:
                    text_group = VGroup(title)
                
                text_group.move_to(ORIGIN)
                
                # 应用动画
                animation_style = validated_params['animation_style']
                if animation_style == "fade":
                    self.play(FadeIn(text_group))
                    self.wait(2)
                    self.play(FadeOut(text_group))
                elif animation_style == "write":
                    self.play(Write(text_group))
                    self.wait(2)
                    self.play(FadeOut(text_group))
                elif animation_style == "slide":
                    text_group.shift(LEFT * 3)
                    self.play(text_group.animate.shift(RIGHT * 3))
                    self.wait(2)
                    self.play(text_group.animate.shift(RIGHT * 3))
        
        return SimpleTextScene


class ListTemplate(VideoTemplate):
    """列表展示模板"""
    
    def get_metadata(self) -> TemplateMetadata:
        return TemplateMetadata(
            id="list_display",
            name="列表展示",
            description="适合展示要点、步骤或清单的模板",
            category="list",
            author="ClipTurbo",
            version="1.0.0",
            tags=["list", "bullet", "steps"],
            duration_range=(15, 60)
        )
    
    def get_parameters(self) -> List[TemplateParameter]:
        return [
            TemplateParameter(
                name="title",
                type=ParameterType.TEXT,
                description="列表标题",
                required=True
            ),
            TemplateParameter(
                name="items",
                type=ParameterType.TEXT,
                description="列表项目（每行一个）",
                required=True
            ),
            TemplateParameter(
                name="max_items_per_screen",
                type=ParameterType.NUMBER,
                description="每屏最大显示项目数",
                default_value=5,
                min_value=1,
                max_value=10
            ),
            TemplateParameter(
                name="item_animation",
                type=ParameterType.CHOICE,
                description="项目出现动画",
                default_value="sequential",
                choices=["sequential", "simultaneous", "typewriter"]
            )
        ]
    
    def create_scene(self, params: Dict[str, Any]) -> Type[Scene]:
        validated_params = self.validate_parameters(params)
        
        class ListScene(Scene):
            def construct(self):
                # 解析列表项
                items_text = validated_params['items']
                items = [item.strip() for item in items_text.split('\n') if item.strip()]
                
                # 创建标题
                title = Text(validated_params['title'], font_size=36)
                title.to_edge(UP, buff=1)
                
                self.play(Write(title))
                self.wait(0.5)
                
                # 创建列表项
                max_items = int(validated_params['max_items_per_screen'])
                animation_style = validated_params['item_animation']
                
                for i in range(0, len(items), max_items):
                    screen_items = items[i:i + max_items]
                    
                    # 创建当前屏幕的项目
                    item_objects = []
                    for j, item in enumerate(screen_items):
                        bullet = Text("•", font_size=24)
                        text = Text(item, font_size=20)
                        text.next_to(bullet, RIGHT, buff=0.2)
                        
                        item_group = VGroup(bullet, text)
                        item_group.shift(DOWN * (j * 0.8 + 1))
                        item_objects.append(item_group)
                    
                    # 应用动画
                    if animation_style == "sequential":
                        for item in item_objects:
                            self.play(FadeIn(item), run_time=0.5)
                    elif animation_style == "simultaneous":
                        self.play(*[FadeIn(item) for item in item_objects])
                    elif animation_style == "typewriter":
                        for item in item_objects:
                            self.play(Write(item), run_time=1)
                    
                    self.wait(2)
                    
                    # 如果还有更多项目，清除当前屏幕
                    if i + max_items < len(items):
                        self.play(*[FadeOut(item) for item in item_objects])
                
                self.wait(1)
        
        return ListScene


class TemplateManager:
    """模板管理器"""
    
    def __init__(self, template_directory: Optional[str] = None):
        self.template_directory = Path(template_directory) if template_directory else None
        self.logger = logging.getLogger(__name__)
        
        # 内置模板
        self.builtin_templates = {
            'simple_text': SimpleTextTemplate(),
            'list_display': ListTemplate(),
        }
        
        # 动态加载双语字幕模板
        try:
            from .bilingual_subtitle_template import BilingualSubtitleTemplate
            self.builtin_templates['bilingual_subtitle'] = BilingualSubtitleTemplate()
        except ImportError:
            self.logger.warning("双语字幕模板加载失败")
        
        # 注册内置模板
        self.builtin_templates_enabled = True
        
        # 自定义模板
        self.custom_templates = {}
        
        # 加载自定义模板
        if self.template_directory and self.template_directory.exists():
            self._load_custom_templates()
    
    def _load_custom_templates(self):
        """加载自定义模板"""
        try:
            for template_file in self.template_directory.glob("*.py"):
                if template_file.name.startswith("_"):
                    continue
                
                # 动态导入模板模块
                spec = importlib.util.spec_from_file_location(
                    template_file.stem, template_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # 查找模板类
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, VideoTemplate) and 
                        obj != VideoTemplate):
                        
                        template_instance = obj()
                        template_id = template_instance.metadata.id
                        self.custom_templates[template_id] = template_instance
                        
                        self.logger.info(f"加载自定义模板: {template_id}")
                        
        except Exception as e:
            self.logger.error(f"加载自定义模板失败: {str(e)}")
    
    def get_template(self, template_id: str) -> Optional[VideoTemplate]:
        """获取模板"""
        # 优先查找自定义模板
        if template_id in self.custom_templates:
            return self.custom_templates[template_id]
        
        # 查找内置模板
        if template_id in self.builtin_templates:
            return self.builtin_templates[template_id]
        
        return None
    
    def list_templates(self, category: Optional[str] = None) -> List[TemplateMetadata]:
        """列出所有模板"""
        all_templates = {**self.builtin_templates, **self.custom_templates}
        
        templates = []
        for template in all_templates.values():
            if category is None or template.metadata.category == category:
                templates.append(template.metadata)
        
        return sorted(templates, key=lambda x: (x.category, x.name))
    
    def get_categories(self) -> List[str]:
        """获取所有模板分类"""
        all_templates = {**self.builtin_templates, **self.custom_templates}
        categories = set(template.metadata.category for template in all_templates.values())
        return sorted(categories)
    
    def create_scene_from_template(
        self, 
        template_id: str, 
        parameters: Dict[str, Any]
    ) -> Optional[Type[Scene]]:
        """从模板创建场景"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板 '{template_id}' 不存在")
        
        try:
            return template.create_scene(parameters)
        except Exception as e:
            self.logger.error(f"创建场景失败: {str(e)}")
            raise
    
    def validate_template_parameters(
        self, 
        template_id: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """验证模板参数"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板 '{template_id}' 不存在")
        
        return template.validate_parameters(parameters)
    
    def get_template_parameters(self, template_id: str) -> List[TemplateParameter]:
        """获取模板参数定义"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板 '{template_id}' 不存在")
        
        return template.parameters
    
    def register_template(self, template: VideoTemplate):
        """注册新模板"""
        template_id = template.metadata.id
        
        if template_id in self.builtin_templates:
            raise ValueError(f"不能覆盖内置模板: {template_id}")
        
        self.custom_templates[template_id] = template
        self.logger.info(f"注册模板: {template_id}")
    
    def unregister_template(self, template_id: str) -> bool:
        """注销模板"""
        if template_id in self.builtin_templates:
            raise ValueError(f"不能注销内置模板: {template_id}")
        
        if template_id in self.custom_templates:
            del self.custom_templates[template_id]
            self.logger.info(f"注销模板: {template_id}")
            return True
        
        return False
    
    def export_template_config(self, template_id: str) -> Dict[str, Any]:
        """导出模板配置"""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"模板 '{template_id}' 不存在")
        
        return {
            'metadata': {
                'id': template.metadata.id,
                'name': template.metadata.name,
                'description': template.metadata.description,
                'category': template.metadata.category,
                'author': template.metadata.author,
                'version': template.metadata.version,
                'tags': template.metadata.tags,
                'duration_range': template.metadata.duration_range,
                'aspect_ratios': template.metadata.aspect_ratios,
                'difficulty': template.metadata.difficulty
            },
            'parameters': [
                {
                    'name': param.name,
                    'type': param.type.value,
                    'description': param.description,
                    'default_value': param.default_value,
                    'required': param.required,
                    'choices': param.choices,
                    'min_value': param.min_value,
                    'max_value': param.max_value,
                    'validation_pattern': param.validation_pattern
                }
                for param in template.parameters
            ]
        }
    
    def search_templates(self, query: str) -> List[TemplateMetadata]:
        """搜索模板"""
        query_lower = query.lower()
        all_templates = {**self.builtin_templates, **self.custom_templates}
        
        matching_templates = []
        for template in all_templates.values():
            metadata = template.metadata
            
            # 搜索名称、描述、标签
            if (query_lower in metadata.name.lower() or
                query_lower in metadata.description.lower() or
                any(query_lower in tag.lower() for tag in metadata.tags)):
                matching_templates.append(metadata)
        
        return sorted(matching_templates, key=lambda x: x.name)
