"""
TTS Service - 文本转语音服务
"""

import asyncio
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import aiohttp
import aiofiles
from pathlib import Path
import hashlib
import tempfile


@dataclass
class Voice:
    """语音配置"""
    id: str
    name: str
    language: str
    gender: str
    description: str
    sample_rate: int = 24000


@dataclass
class TTSResult:
    """TTS合成结果"""
    audio_file: str
    duration: float
    voice_used: Voice
    text_length: int
    file_size: int


class TTSProvider(ABC):
    """TTS提供者抽象基类"""
    
    @abstractmethod
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        pitch: float = 1.0,
        output_file: Optional[str] = None
    ) -> TTSResult:
        pass
    
    @abstractmethod
    def get_available_voices(self) -> List[Voice]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass


class EdgeTTSProvider(TTSProvider):
    """Edge TTS提供者 - 免费的微软语音服务"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Edge TTS支持的语音
        self.voices = [
            Voice("zh-CN-XiaoxiaoNeural", "晓晓", "zh-CN", "female", "温柔女声"),
            Voice("zh-CN-YunxiNeural", "云希", "zh-CN", "male", "成熟男声"),
            Voice("zh-CN-YunyangNeural", "云扬", "zh-CN", "male", "青年男声"),
            Voice("zh-CN-XiaoyiNeural", "晓伊", "zh-CN", "female", "甜美女声"),
            Voice("zh-CN-YunjianNeural", "云健", "zh-CN", "male", "稳重男声"),
            Voice("zh-CN-XiaochenNeural", "晓辰", "zh-CN", "female", "活泼女声"),
            Voice("zh-CN-XiaohanNeural", "晓涵", "zh-CN", "female", "知性女声"),
            Voice("zh-CN-XiaomengNeural", "晓梦", "zh-CN", "female", "少女声"),
            Voice("zh-CN-XiaomoNeural", "晓墨", "zh-CN", "female", "成熟女声"),
            Voice("zh-CN-XiaoqiuNeural", "晓秋", "zh-CN", "female", "温暖女声"),
            Voice("zh-CN-XiaoruiNeural", "晓睿", "zh-CN", "female", "清脆女声"),
            Voice("zh-CN-XiaoshuangNeural", "晓双", "zh-CN", "female", "双语女声"),
            Voice("zh-CN-XiaoxuanNeural", "晓萱", "zh-CN", "female", "优雅女声"),
            Voice("zh-CN-XiaoyanNeural", "晓颜", "zh-CN", "female", "亲切女声"),
            Voice("zh-CN-XiaoyouNeural", "晓悠", "zh-CN", "female", "悠扬女声"),
            Voice("zh-CN-XiaozhenNeural", "晓甄", "zh-CN", "female", "专业女声"),
            Voice("zh-CN-YunfengNeural", "云枫", "zh-CN", "male", "磁性男声"),
            Voice("zh-CN-YunhaoNeural", "云皓", "zh-CN", "male", "阳光男声"),
            Voice("zh-CN-YunjieNeural", "云杰", "zh-CN", "male", "商务男声"),
            
            # 英文语音
            Voice("en-US-AriaNeural", "Aria", "en-US", "female", "Natural female voice"),
            Voice("en-US-DavisNeural", "Davis", "en-US", "male", "Natural male voice"),
            Voice("en-US-GuyNeural", "Guy", "en-US", "male", "Casual male voice"),
            Voice("en-US-JaneNeural", "Jane", "en-US", "female", "Professional female voice"),
            Voice("en-US-JasonNeural", "Jason", "en-US", "male", "Energetic male voice"),
            Voice("en-US-JennyNeural", "Jenny", "en-US", "female", "Friendly female voice"),
            Voice("en-US-NancyNeural", "Nancy", "en-US", "female", "Warm female voice"),
            Voice("en-US-TonyNeural", "Tony", "en-US", "male", "Professional male voice"),
        ]
    
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        pitch: float = 1.0,
        output_file: Optional[str] = None
    ) -> TTSResult:
        try:
            import edge_tts
            
            # 生成输出文件名
            if not output_file:
                text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                output_file = f"{tempfile.gettempdir()}/tts_{text_hash}_{voice_id}.mp3"
            
            # 构建SSML
            ssml_text = self._build_ssml(text, voice_id, speed, pitch)
            
            # 创建TTS通信对象
            communicate = edge_tts.Communicate(ssml_text, voice_id)
            
            # 合成语音
            await communicate.save(output_file)
            
            # 获取语音信息
            voice = self._get_voice_by_id(voice_id)
            file_size = Path(output_file).stat().st_size
            
            # 估算时长（简单估算）
            duration = len(text) / (3 * speed)  # 假设每秒3个字
            
            return TTSResult(
                audio_file=output_file,
                duration=duration,
                voice_used=voice,
                text_length=len(text),
                file_size=file_size
            )
            
        except ImportError:
            raise Exception("需要安装 edge-tts: pip install edge-tts")
        except Exception as e:
            self.logger.error(f"Edge TTS合成失败: {str(e)}")
            raise
    
    def _build_ssml(self, text: str, voice_id: str, speed: float, pitch: float) -> str:
        """构建SSML格式的文本"""
        # 转换速度和音调参数
        speed_str = f"{speed:.1f}" if speed != 1.0 else "medium"
        pitch_str = f"{pitch:.1f}" if pitch != 1.0 else "medium"
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="zh-CN">
            <voice name="{voice_id}">
                <prosody rate="{speed_str}" pitch="{pitch_str}">
                    {text}
                </prosody>
            </voice>
        </speak>
        """
        return ssml.strip()
    
    def _get_voice_by_id(self, voice_id: str) -> Voice:
        """根据ID获取语音配置"""
        for voice in self.voices:
            if voice.id == voice_id:
                return voice
        
        # 返回默认语音
        return self.voices[0]
    
    def get_available_voices(self) -> List[Voice]:
        return self.voices.copy()
    
    def is_available(self) -> bool:
        try:
            import edge_tts
            return True
        except ImportError:
            return False


class AzureTTSProvider(TTSProvider):
    """Azure TTS提供者"""
    
    def __init__(self, subscription_key: str, region: str):
        self.subscription_key = subscription_key
        self.region = region
        self.base_url = f"https://{region}.tts.speech.microsoft.com"
        self.logger = logging.getLogger(__name__)
        
        # Azure支持的语音（部分）
        self.voices = [
            Voice("zh-CN-XiaoxiaoNeural", "晓晓", "zh-CN", "female", "Azure晓晓"),
            Voice("zh-CN-YunxiNeural", "云希", "zh-CN", "male", "Azure云希"),
            Voice("en-US-AriaNeural", "Aria", "en-US", "female", "Azure Aria"),
            Voice("en-US-DavisNeural", "Davis", "en-US", "male", "Azure Davis"),
        ]
    
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        speed: float = 1.0,
        pitch: float = 1.0,
        output_file: Optional[str] = None
    ) -> TTSResult:
        try:
            # 生成输出文件名
            if not output_file:
                text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                output_file = f"{tempfile.gettempdir()}/azure_tts_{text_hash}.wav"
            
            # 构建SSML
            ssml = self._build_ssml(text, voice_id, speed, pitch)
            
            # 获取访问令牌
            token = await self._get_access_token()
            
            # 合成语音
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/ssml+xml',
                'X-Microsoft-OutputFormat': 'audio-24khz-48kbitrate-mono-mp3'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/cognitiveservices/v1",
                    headers=headers,
                    data=ssml.encode('utf-8')
                ) as response:
                    if response.status == 200:
                        # 保存音频文件
                        async with aiofiles.open(output_file, 'wb') as f:
                            async for chunk in response.content.iter_chunked(8192):
                                await f.write(chunk)
                        
                        # 返回结果
                        voice = self._get_voice_by_id(voice_id)
                        file_size = Path(output_file).stat().st_size
                        duration = len(text) / (3 * speed)
                        
                        return TTSResult(
                            audio_file=output_file,
                            duration=duration,
                            voice_used=voice,
                            text_length=len(text),
                            file_size=file_size
                        )
                    else:
                        raise Exception(f"Azure TTS API错误: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Azure TTS合成失败: {str(e)}")
            raise
    
    async def _get_access_token(self) -> str:
        """获取Azure访问令牌"""
        token_url = f"https://{self.region}.api.cognitive.microsoft.com/sts/v1.0/issueToken"
        
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, headers=headers) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    raise Exception(f"获取Azure令牌失败: {response.status}")
    
    def _build_ssml(self, text: str, voice_id: str, speed: float, pitch: float) -> str:
        """构建SSML"""
        return f"""
        <speak version='1.0' xml:lang='zh-CN' xmlns='http://www.w3.org/2001/10/synthesis'>
            <voice name='{voice_id}'>
                <prosody rate='{speed:.1f}' pitch='{pitch:.1f}'>
                    {text}
                </prosody>
            </voice>
        </speak>
        """
    
    def _get_voice_by_id(self, voice_id: str) -> Voice:
        """根据ID获取语音配置"""
        for voice in self.voices:
            if voice.id == voice_id:
                return voice
        return self.voices[0]
    
    def get_available_voices(self) -> List[Voice]:
        return self.voices.copy()
    
    def is_available(self) -> bool:
        return bool(self.subscription_key and self.region)


class TTSService:
    """TTS服务管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化TTS提供者
        self.providers = []
        self._init_providers()
        
        # 当前使用的提供者
        self.current_provider = self.providers[0] if self.providers else None
        
        # 缓存
        self._cache = {}
        self.cache_enabled = config.get('cache_enabled', True)
        
        # 输出目录
        self.output_dir = Path(config.get('output_dir', tempfile.gettempdir()))
        self.output_dir.mkdir(exist_ok=True)
    
    def _init_providers(self):
        """初始化TTS提供者"""
        # Edge TTS提供者（免费）
        try:
            provider = EdgeTTSProvider()
            if provider.is_available():
                self.providers.append(provider)
                self.logger.info("Edge TTS提供者初始化成功")
        except Exception as e:
            self.logger.warning(f"Edge TTS提供者初始化失败: {str(e)}")
        
        # Azure TTS提供者
        azure_config = self.config.get('azure', {})
        if azure_config.get('subscription_key') and azure_config.get('region'):
            try:
                provider = AzureTTSProvider(
                    subscription_key=azure_config['subscription_key'],
                    region=azure_config['region']
                )
                self.providers.append(provider)
                self.logger.info("Azure TTS提供者初始化成功")
            except Exception as e:
                self.logger.warning(f"Azure TTS提供者初始化失败: {str(e)}")
    
    async def synthesize(
        self,
        text: str,
        language: str = 'zh-CN',
        voice: str = 'default',
        speed: float = 1.0,
        pitch: float = 1.0,
        provider_name: Optional[str] = None
    ) -> str:
        """
        合成语音
        
        Args:
            text: 要合成的文本
            language: 语言代码
            voice: 语音ID或类型
            speed: 语速 (0.5-2.0)
            pitch: 音调 (0.5-2.0)
            provider_name: 指定的提供者名称
            
        Returns:
            生成的音频文件路径
        """
        if not text.strip():
            raise ValueError("文本不能为空")
        
        # 检查缓存
        cache_key = f"{hash(text)}_{language}_{voice}_{speed}_{pitch}"
        if self.cache_enabled and cache_key in self._cache:
            cached_file = self._cache[cache_key]
            if Path(cached_file).exists():
                return cached_file
        
        # 选择提供者
        provider = self._select_provider(provider_name)
        if not provider:
            raise Exception("没有可用的TTS提供者")
        
        # 选择语音
        voice_id = self._select_voice(provider, language, voice)
        
        # 生成输出文件路径
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        output_file = self.output_dir / f"tts_{text_hash}_{voice_id.replace('-', '_')}.mp3"
        
        try:
            # 合成语音
            result = await provider.synthesize(
                text=text,
                voice_id=voice_id,
                speed=speed,
                pitch=pitch,
                output_file=str(output_file)
            )
            
            # 缓存结果
            if self.cache_enabled:
                self._cache[cache_key] = result.audio_file
            
            self.logger.info(f"TTS合成成功: {result.audio_file}")
            return result.audio_file
            
        except Exception as e:
            self.logger.error(f"TTS合成失败: {str(e)}")
            # 尝试备用提供者
            return await self._fallback_synthesize(text, language, voice, speed, pitch, provider)
    
    def _select_provider(self, provider_name: Optional[str]) -> Optional[TTSProvider]:
        """选择TTS提供者"""
        if provider_name:
            for provider in self.providers:
                if provider_name.lower() in provider.__class__.__name__.lower():
                    if provider.is_available():
                        return provider
            return None
        
        # 返回第一个可用的提供者
        for provider in self.providers:
            if provider.is_available():
                return provider
        
        return None
    
    def _select_voice(self, provider: TTSProvider, language: str, voice: str) -> str:
        """选择合适的语音"""
        available_voices = provider.get_available_voices()
        
        # 如果指定了具体的语音ID
        for v in available_voices:
            if v.id == voice:
                return voice
        
        # 根据语言和性别选择
        if voice == 'default':
            # 选择默认语音
            for v in available_voices:
                if v.language == language:
                    return v.id
        elif voice in ['female', 'male']:
            # 选择指定性别的语音
            for v in available_voices:
                if v.language == language and v.gender == voice:
                    return v.id
        
        # 返回第一个匹配语言的语音
        for v in available_voices:
            if v.language == language:
                return v.id
        
        # 返回第一个可用语音
        return available_voices[0].id if available_voices else "zh-CN-XiaoxiaoNeural"
    
    async def _fallback_synthesize(
        self,
        text: str,
        language: str,
        voice: str,
        speed: float,
        pitch: float,
        failed_provider: TTSProvider
    ) -> str:
        """备用合成方法"""
        for provider in self.providers:
            if provider != failed_provider and provider.is_available():
                try:
                    voice_id = self._select_voice(provider, language, voice)
                    
                    text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
                    output_file = self.output_dir / f"tts_fallback_{text_hash}.mp3"
                    
                    result = await provider.synthesize(
                        text=text,
                        voice_id=voice_id,
                        speed=speed,
                        pitch=pitch,
                        output_file=str(output_file)
                    )
                    
                    return result.audio_file
                    
                except Exception as e:
                    self.logger.warning(f"备用TTS提供者失败: {str(e)}")
                    continue
        
        raise Exception("所有TTS提供者都不可用")
    
    async def batch_synthesize(
        self,
        texts: List[str],
        language: str = 'zh-CN',
        voice: str = 'default',
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> List[str]:
        """批量合成语音"""
        tasks = [
            self.synthesize(text, language, voice, speed, pitch)
            for text in texts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        audio_files = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"合成文本 '{texts[i][:50]}...' 失败: {str(result)}")
                audio_files.append("")
            else:
                audio_files.append(result)
        
        return audio_files
    
    def get_available_voices(self, language: Optional[str] = None) -> List[Voice]:
        """获取可用的语音列表"""
        if not self.current_provider:
            return []
        
        voices = self.current_provider.get_available_voices()
        
        if language:
            voices = [v for v in voices if v.language == language]
        
        return voices
    
    def get_supported_languages(self) -> List[str]:
        """获取支持的语言列表"""
        if not self.current_provider:
            return []
        
        voices = self.current_provider.get_available_voices()
        languages = list(set(v.language for v in voices))
        
        return sorted(languages)
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return any(provider.is_available() for provider in self.providers)
    
    def get_provider_status(self) -> Dict[str, bool]:
        """获取所有提供者状态"""
        return {
            provider.__class__.__name__: provider.is_available()
            for provider in self.providers
        }
    
    def clear_cache(self):
        """清空TTS缓存"""
        self._cache.clear()
        self.logger.info("TTS缓存已清空")
    
    def cleanup_old_files(self, days: int = 7):
        """清理旧的音频文件"""
        import time
        
        current_time = time.time()
        cutoff_time = current_time - (days * 24 * 60 * 60)
        
        cleaned_count = 0
        for file_path in self.output_dir.glob("tts_*.mp3"):
            if file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    cleaned_count += 1
                except Exception as e:
                    self.logger.warning(f"删除文件失败 {file_path}: {str(e)}")
        
        self.logger.info(f"清理了 {cleaned_count} 个旧音频文件")
