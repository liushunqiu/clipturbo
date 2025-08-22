"""
双语字幕视频模板 - 支持中英文字幕同时显示
参考短视频平台的双语字幕样式
"""

from manim import *
from typing import Dict, Any, List, Optional, Tuple
import asyncio
from .template_system import VideoTemplate, TemplateParameter, ParameterType, TemplateMetadata
from ..ai_services.translation_service import TranslationService
from ..ai_services.emoji_strategy_manager import EmojiStrategyManager, EmojiStrategyConfig, EmojiStrategy

class BilingualSubtitleTemplate(VideoTemplate):
    """双语字幕模板"""
    
    def __init__(self):
        super().__init__()
        self.translation_service = TranslationService()
        self.emoji_strategy_manager = EmojiStrategyManager()
    
    def get_metadata(self) -> TemplateMetadata:
        return TemplateMetadata(
            id="bilingual_subtitle",
            name="双语字幕模板",
            description="支持中英文双语字幕显示，适合教育和娱乐内容",
            category="subtitle",
            author="ClipTurbo Team",
            version="1.0.0",
            tags=["双语", "字幕", "教育", "娱乐"],
            preview_image="bilingual_subtitle_preview.png",
            duration_range=(10, 120),
            aspect_ratios=["16:9", "9:16", "1:1"],
            difficulty="intermediate"
        )
    
    def get_parameters(self) -> List[TemplateParameter]:
        return [
            TemplateParameter(
                name="script_segments",
                type=ParameterType.TEXT,
                description="分段的文案内容，每段包含中文、英文和配图",
                required=True,
                default_value=[]
            ),
            TemplateParameter(
                name="background_color",
                type=ParameterType.COLOR,
                description="视频背景颜色",
                required=False,
                default_value="#000000"
            ),
            TemplateParameter(
                name="chinese_font_size",
                type=ParameterType.NUMBER,
                description="中文字幕字体大小",
                required=False,
                default_value=48,
                min_value=24,
                max_value=72
            ),
            TemplateParameter(
                name="english_font_size",
                type=ParameterType.NUMBER,
                description="英文字幕字体大小",
                required=False,
                default_value=36,
                min_value=18,
                max_value=54
            ),
            TemplateParameter(
                name="segment_duration",
                type=ParameterType.DURATION,
                description="每个文案段落的显示时间（秒）",
                required=False,
                default_value=3.0,
                min_value=1.0,
                max_value=10.0
            ),
            TemplateParameter(
                name="show_emoji",
                type=ParameterType.BOOLEAN,
                description="是否在右侧显示相关表情或图标",
                required=False,
                default_value=True
            ),
            TemplateParameter(
                name="highlight_style",
                type=ParameterType.CHOICE,
                description="文字高亮显示样式",
                required=False,
                default_value="glow",
                choices=["glow", "underline", "background", "scale"]
            )
        ]
    
    async def prepare_content(self, script: str, **kwargs) -> List[Dict[str, Any]]:
        """准备双语内容"""
        # 将脚本分段
        segments = self._split_script_into_segments(script)
        
        prepared_segments = []
        for i, segment in enumerate(segments):
            # 翻译中文到英文
            try:
                if self._is_chinese(segment):
                    english_text = await self.translation_service.translate(
                        segment, "zh-CN", "en"
                    )
                    chinese_text = segment
                else:
                    chinese_text = await self.translation_service.translate(
                        segment, "en", "zh-CN"
                    )
                    english_text = segment
            except Exception as e:
                # 翻译失败时的处理
                if self._is_chinese(segment):
                    chinese_text = segment
                    english_text = f"Translation failed: {str(e)}"
                else:
                    english_text = segment
                    chinese_text = f"翻译失败: {str(e)}"
            
            # 使用智能表情匹配
            emoji_match = await self.emoji_matcher.get_smart_emoji(segment)
            emoji = emoji_match.emoji
            
            prepared_segments.append({
                "chinese": chinese_text,
                "english": english_text,
                "emoji": emoji,
                "index": i
            })
        
        return prepared_segments
    
    def create_scene(self, **parameters) -> Scene:
        """创建双语字幕场景"""
        return BilingualSubtitleScene(**parameters)
    
    def _split_script_into_segments(self, script: str) -> List[str]:
        """将脚本分割成合适的段落"""
        # 按句号、问号、感叹号分割
        import re
        segments = re.split(r'[。！？.!?]', script.strip())
        
        # 过滤空段落并添加标点
        result = []
        for segment in segments:
            segment = segment.strip()
            if segment:
                # 根据内容添加合适的标点
                if self._is_question(segment):
                    segment += "？" if self._is_chinese(segment) else "?"
                elif self._is_exclamation(segment):
                    segment += "！" if self._is_chinese(segment) else "!"
                else:
                    segment += "。" if self._is_chinese(segment) else "."
                result.append(segment)
        
        return result
    
    def _is_chinese(self, text: str) -> bool:
        """检测文本是否主要为中文"""
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len(text.replace(' ', ''))
        return chinese_chars / max(total_chars, 1) > 0.3
    
    def _is_question(self, text: str) -> bool:
        """检测是否为疑问句"""
        question_words = ['什么', '哪里', '怎么', '为什么', '吗', 'what', 'where', 'how', 'why', 'when', 'who']
        return any(word in text.lower() for word in question_words)
    
    def _is_exclamation(self, text: str) -> bool:
        """检测是否为感叹句"""
        exclamation_words = ['太', '真', '好', '哇', 'wow', 'amazing', 'great', 'awesome']
        return any(word in text.lower() for word in exclamation_words)
    
    def _select_emoji_for_text(self, text: str) -> str:
        """根据文本内容选择合适的表情"""
        text_lower = text.lower()
        
        # 情感词汇映射
        emoji_mapping = {
            # 积极情感
            '开心': '😊', '高兴': '😄', '快乐': '😃', '笑': '😂',
            'happy': '😊', 'smile': '😄', 'joy': '😃', 'laugh': '😂',
            
            # 消极情感
            '难过': '😢', '伤心': '😭', '生气': '😠', '愤怒': '😡',
            'sad': '😢', 'cry': '😭', 'angry': '😠', 'mad': '😡',
            
            # 惊讶
            '惊讶': '😲', '震惊': '😱', '哇': '😮',
            'surprise': '😲', 'shock': '😱', 'wow': '😮',
            
            # 思考
            '思考': '🤔', '想': '💭', '考虑': '🤔',
            'think': '🤔', 'consider': '💭', 'wonder': '🤔',
            
            # 爱心
            '爱': '❤️', '喜欢': '💕', '心': '💖',
            'love': '❤️', 'like': '💕', 'heart': '💖',
            
            # 工作学习
            '工作': '💼', '学习': '📚', '书': '📖', '电脑': '💻',
            'work': '💼', 'study': '📚', 'book': '📖', 'computer': '💻',
            
            # 时间
            '时间': '⏰', '钟': '🕐', '日子': '📅',
            'time': '⏰', 'clock': '🕐', 'day': '📅',
            
            # 电话通讯
            '电话': '📞', '手机': '📱', '通话': '☎️',
            'phone': '📞', 'call': '☎️', 'mobile': '📱',
            
            # 动物
            '狗': '🐕', '猫': '🐱', '鸟': '🐦',
            'dog': '🐕', 'cat': '🐱', 'bird': '🐦'
        }
        
        # 查找匹配的表情
        for keyword, emoji in emoji_mapping.items():
            if keyword in text_lower:
                return emoji
        
        # 默认表情
        return '😊'


class BilingualSubtitleScene(Scene):
    """双语字幕场景"""
    
    def __init__(self, script_segments=None, background_color="#000000", 
                 chinese_font_size=48, english_font_size=36, 
                 segment_duration=3.0, show_emoji=True, 
                 highlight_style="glow", **kwargs):
        super().__init__(**kwargs)
        self.script_segments = script_segments or []
        self.background_color = background_color
        self.chinese_font_size = chinese_font_size
        self.english_font_size = english_font_size
        self.segment_duration = segment_duration
        self.show_emoji = show_emoji
        self.highlight_style = highlight_style
    
    def construct(self):
        """构建场景"""
        # 设置背景
        self.camera.background_color = self.background_color
        
        if not self.script_segments:
            # 如果没有提供片段，显示示例内容
            self.script_segments = [
                {
                    "chinese": "别总盯着孩子，先过好你自己的日子",
                    "english": "Stop obsessing over your kids, live your own life first",
                    "emoji": "☀️",
                    "index": 0
                },
                {
                    "chinese": "是不是又在守着电话，等孩子那半个月才来一次的问候？",
                    "english": "Are you waiting by the phone again for that biweekly call from your child?",
                    "emoji": "📞",
                    "index": 1
                },
                {
                    "chinese": "一接通，三句话问不出个所以然，就把电话给挂了",
                    "english": "After three awkward sentences, they hang up without saying much",
                    "emoji": "😤",
                    "index": 2
                },
                {
                    "chinese": "然后自己在这边生半天气，觉得养了个白眼狼？",
                    "english": "Then you sulk, feeling like you raised an ungrateful child",
                    "emoji": "🐺",
                    "index": 3
                }
            ]
        
        # 为每个片段创建动画
        for segment in self.script_segments:
            self.animate_segment(segment)
    
    def animate_segment(self, segment: Dict[str, Any]):
        """为单个片段创建动画"""
        # 创建中文文本
        chinese_text = Text(
            segment["chinese"],
            font_size=self.chinese_font_size,
            color=WHITE,
            font="SimHei"  # 中文字体
        ).move_to(UP * 0.5)
        
        # 创建英文文本
        english_text = Text(
            segment["english"],
            font_size=self.english_font_size,
            color="#CCCCCC",  # 稍微暗一点的颜色
            font="Arial"
        ).move_to(DOWN * 0.8)
        
        # 创建表情图标
        emoji_text = None
        if self.show_emoji and segment.get("emoji"):
            emoji_text = Text(
                segment["emoji"],
                font_size=64
            ).move_to(RIGHT * 4 + UP * 0.5)
        
        # 应用高亮效果
        if self.highlight_style == "glow":
            chinese_text.add_background_rectangle(
                color=YELLOW, opacity=0.3, buff=0.1
            )
        elif self.highlight_style == "underline":
            underline = Line(
                chinese_text.get_left() + DOWN * 0.2,
                chinese_text.get_right() + DOWN * 0.2,
                color=YELLOW,
                stroke_width=3
            )
        
        # 动画序列
        animations = []
        
        # 1. 淡入效果
        animations.extend([
            FadeIn(chinese_text, shift=UP * 0.3),
            FadeIn(english_text, shift=UP * 0.3)
        ])
        
        if emoji_text:
            animations.append(FadeIn(emoji_text, shift=LEFT * 0.5))
        
        if self.highlight_style == "underline":
            animations.append(Create(underline))
        
        # 播放淡入动画
        self.play(*animations, run_time=0.8)
        
        # 2. 保持显示
        self.wait(self.segment_duration - 1.6)  # 减去淡入淡出时间
        
        # 3. 淡出效果
        fade_out_animations = [
            FadeOut(chinese_text, shift=DOWN * 0.3),
            FadeOut(english_text, shift=DOWN * 0.3)
        ]
        
        if emoji_text:
            fade_out_animations.append(FadeOut(emoji_text, shift=RIGHT * 0.5))
        
        if self.highlight_style == "underline":
            fade_out_animations.append(FadeOut(underline))
        
        self.play(*fade_out_animations, run_time=0.8)


# 注册模板
def register_bilingual_template():
    """注册双语字幕模板"""
    from .template_system import TemplateManager
    
    template = BilingualSubtitleTemplate()
    # 这里应该通过模板管理器注册
    # TemplateManager.register_template(template)
    return template

if __name__ == "__main__":
    # 测试场景
    scene = BilingualSubtitleScene()
    scene.render()
