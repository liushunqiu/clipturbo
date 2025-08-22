"""
AI Orchestrator - 协调所有AI服务的核心模块

该模块是ClipTurbo的AI服务中枢，负责统一管理和协调所有AI服务，
包括内容生成、翻译、图标匹配和TTS语音合成。它提供了一个统一的接口
来处理视频内容生成的完整AI流程。

主要功能:
- 内容生成：根据主题生成视频文案
- 翻译处理：多语言翻译支持
- 图标匹配：根据内容自动匹配图标
- TTS合成：文本转语音合成
- 缓存管理：智能缓存AI处理结果
- 错误处理：完善的错误恢复机制
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import logging

from .content_generator import ContentGenerator
from .translation_service import TranslationService
from .icon_matcher import IconMatcher
from .tts_service import TTSService


class ProcessingStage(Enum):
    """AI处理阶段枚举
    
    定义了视频内容生成过程中的各个处理阶段，用于追踪进度和状态。
    
    Attributes:
        CONTENT_GENERATION: 内容生成阶段 - 生成视频文案
        TRANSLATION: 翻译处理阶段 - 多语言翻译
        ICON_MATCHING: 图标匹配阶段 - 自动匹配相关图标
        TTS_SYNTHESIS: TTS合成阶段 - 文本转语音合成
        COMPLETED: 完成阶段 - 所有处理已完成
    """
    CONTENT_GENERATION = "content_generation"
    TRANSLATION = "translation"
    ICON_MATCHING = "icon_matching"
    TTS_SYNTHESIS = "tts_synthesis"
    COMPLETED = "completed"


@dataclass
class ProcessingResult:
    """AI处理结果数据结构
    
    封装了AI服务的处理结果，包含成功状态、处理数据和错误信息。
    
    Attributes:
        stage: 处理阶段
        success: 是否成功
        data: 处理结果数据
        error: 错误信息（如果有）
        processing_time: 处理耗时（秒）
    """
    stage: ProcessingStage
    success: bool
    data: Any
    error: Optional[str] = None
    processing_time: float = 0.0


@dataclass
class VideoContent:
    """视频内容数据结构
    
    表示一个完整的视频内容，包含标题、脚本、语言、风格等信息。
    这是AI处理流程的核心数据结构，在各个服务间传递。
    
    Attributes:
        title: 视频标题
        script: 视频脚本正文
        language: 语言代码（默认zh-CN）
        style: 内容风格（默认default）
        target_duration: 目标时长（秒，默认60）
        translated_script: 翻译后的脚本（可选）
        icons: 图标文件路径列表（可选）
        audio_file: 音频文件路径（可选）
    """
    title: str
    script: str
    language: str = "zh-CN"
    style: str = "default"
    target_duration: int = 60  # 秒
    translated_script: Optional[str] = None
    icons: Optional[List[str]] = None
    audio_file: Optional[str] = None


class AIOrchestrator:
    """AI服务协调器 - 统一管理和协调所有AI服务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化各个AI服务
        self.content_generator = ContentGenerator(config.get('content_generator', {}))
        self.translation_service = TranslationService(config.get('translation', {}))
        self.icon_matcher = IconMatcher(config.get('icon_matcher', {}))
        self.tts_service = TTSService(config.get('tts', {}))
        
        # 处理缓存
        self._cache = {}
        
    async def process_video_content(
        self, 
        topic: str, 
        requirements: Dict[str, Any]
    ) -> VideoContent:
        """
        完整的视频内容处理流程
        
        Args:
            topic: 视频主题
            requirements: 处理要求 (语言、风格、时长等)
            
        Returns:
            VideoContent: 处理完成的视频内容
        """
        self.logger.info(f"开始处理视频内容: {topic}")
        
        # 创建视频内容对象
        content = VideoContent(
            title=topic,
            script="",
            language=requirements.get('language', 'zh-CN'),
            style=requirements.get('style', 'default'),
            target_duration=requirements.get('duration', 60)
        )
        
        try:
            # 阶段1: 内容生成
            result = await self._generate_content(topic, requirements)
            if result.success:
                content.script = result.data['script']
                content.title = result.data.get('title', topic)
            else:
                raise Exception(f"内容生成失败: {result.error}")
            
            # 阶段2: 翻译 (如果需要)
            if requirements.get('translate_to'):
                result = await self._translate_content(content, requirements['translate_to'])
                if result.success:
                    content.translated_script = result.data
                else:
                    self.logger.warning(f"翻译失败: {result.error}")
            
            # 阶段3: 图标匹配
            result = await self._match_icons(content)
            if result.success:
                content.icons = result.data
            else:
                self.logger.warning(f"图标匹配失败: {result.error}")
            
            # 阶段4: TTS合成
            result = await self._synthesize_speech(content, requirements)
            if result.success:
                content.audio_file = result.data
            else:
                self.logger.warning(f"语音合成失败: {result.error}")
            
            self.logger.info("视频内容处理完成")
            return content
            
        except Exception as e:
            self.logger.error(f"视频内容处理失败: {str(e)}")
            raise
    
    async def _generate_content(
        self, 
        topic: str, 
        requirements: Dict[str, Any]
    ) -> ProcessingResult:
        """生成视频内容"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # 检查缓存
            cache_key = f"content_{hash(topic + str(requirements))}"
            if cache_key in self._cache:
                return self._cache[cache_key]
            
            # 生成内容
            result = await self.content_generator.generate_video_script(
                topic=topic,
                style=requirements.get('style', 'default'),
                duration=requirements.get('duration', 60),
                language=requirements.get('language', 'zh-CN')
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            processing_result = ProcessingResult(
                stage=ProcessingStage.CONTENT_GENERATION,
                success=True,
                data=result,
                processing_time=processing_time
            )
            
            # 缓存结果
            self._cache[cache_key] = processing_result
            
            return processing_result
            
        except Exception as e:
            return ProcessingResult(
                stage=ProcessingStage.CONTENT_GENERATION,
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _translate_content(
        self, 
        content: VideoContent, 
        target_language: str
    ) -> ProcessingResult:
        """翻译内容"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            translated_text = await self.translation_service.translate(
                text=content.script,
                source_lang=content.language,
                target_lang=target_language
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return ProcessingResult(
                stage=ProcessingStage.TRANSLATION,
                success=True,
                data=translated_text,
                processing_time=processing_time
            )
            
        except Exception as e:
            return ProcessingResult(
                stage=ProcessingStage.TRANSLATION,
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _match_icons(self, content: VideoContent) -> ProcessingResult:
        """匹配图标和图片"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            icons = await self.icon_matcher.find_matching_icons(
                text=content.script,
                style=content.style,
                count=5
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return ProcessingResult(
                stage=ProcessingStage.ICON_MATCHING,
                success=True,
                data=icons,
                processing_time=processing_time
            )
            
        except Exception as e:
            return ProcessingResult(
                stage=ProcessingStage.ICON_MATCHING,
                success=False,
                data=None,
                error=str(e)
            )
    
    async def _synthesize_speech(
        self, 
        content: VideoContent, 
        requirements: Dict[str, Any]
    ) -> ProcessingResult:
        """合成语音"""
        try:
            start_time = asyncio.get_event_loop().time()
            
            # 选择要合成的文本
            text_to_synthesize = content.translated_script or content.script
            
            audio_file = await self.tts_service.synthesize(
                text=text_to_synthesize,
                language=requirements.get('tts_language', content.language),
                voice=requirements.get('voice', 'default'),
                speed=requirements.get('speed', 1.0)
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            return ProcessingResult(
                stage=ProcessingStage.TTS_SYNTHESIS,
                success=True,
                data=audio_file,
                processing_time=processing_time
            )
            
        except Exception as e:
            return ProcessingResult(
                stage=ProcessingStage.TTS_SYNTHESIS,
                success=False,
                data=None,
                error=str(e)
            )
    
    async def batch_process(
        self, 
        topics: List[str], 
        requirements: Dict[str, Any]
    ) -> List[VideoContent]:
        """批量处理多个视频内容"""
        self.logger.info(f"开始批量处理 {len(topics)} 个视频")
        
        # 并发处理
        tasks = [
            self.process_video_content(topic, requirements) 
            for topic in topics
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_contents = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"处理主题 '{topics[i]}' 失败: {str(result)}")
            else:
                processed_contents.append(result)
        
        self.logger.info(f"批量处理完成，成功处理 {len(processed_contents)} 个视频")
        return processed_contents
    
    def get_processing_status(self) -> Dict[str, Any]:
        """获取处理状态统计"""
        return {
            'cache_size': len(self._cache),
            'services_status': {
                'content_generator': self.content_generator.is_available(),
                'translation_service': self.translation_service.is_available(),
                'icon_matcher': self.icon_matcher.is_available(),
                'tts_service': self.tts_service.is_available()
            }
        }
    
    def clear_cache(self):
        """清空缓存"""
        self._cache.clear()
        self.logger.info("AI处理缓存已清空")
