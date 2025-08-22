"""
Translation Service - 多语言翻译服务
"""

import asyncio
from typing import Dict, Any, Optional, List
import logging
import json
import requests
from dataclasses import dataclass


@dataclass
class LanguageInfo:
    """语言信息"""
    code: str
    name: str
    native_name: str




class ModelScopeTranslateProvider:
    """ModelScope翻译提供者"""
    
    def __init__(self, sdk_token: str = "ms-c0d318a3-9811-4fac-8f4a-353383a30edd"):
        self.sdk_token = sdk_token
        # 修正API URL，使用正确的模型接口
        self.api_url = "https://api-inference.modelscope.cn/api-inference/v1/models/iic/nlp_csanmt_translation_en2zh"
        self.logger = logging.getLogger(__name__)
        
        # ModelScope支持的语言（主要支持英中互译）
        self.supported_languages = [
            LanguageInfo("zh-CN", "Chinese (Simplified)", "简体中文"),
            LanguageInfo("en", "English", "English"),
        ]
    
    def _query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """调用ModelScope API"""
        headers = {
            "Authorization": f"Bearer {self.sdk_token}",
            "Content-Type": "application/json"
        }
        data = json.dumps(payload)
        
        self.logger.info(f"调用ModelScope API: {self.api_url}")
        self.logger.info(f"请求数据: {data}")
        
        try:
            response = requests.post(self.api_url, headers=headers, data=data, timeout=30)
            response.raise_for_status()
            result = json.loads(response.content.decode("utf-8"))
            self.logger.info(f"API响应: {result}")
            return result
        except requests.exceptions.RequestException as e:
            self.logger.error(f"HTTP请求失败: {e}")
            raise Exception(f"ModelScope API请求失败: {e}")
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON解析失败: {e}")
            raise Exception(f"ModelScope API响应解析失败: {e}")
    
    async def translate(
        self, 
        text: str, 
        source_lang: str, 
        target_lang: str
    ) -> str:
        try:
            # ModelScope主要支持英中互译
            if source_lang.startswith('zh') and target_lang == 'en':
                raise Exception(f"ModelScope翻译暂不支持中译英，仅支持英译中")
            elif source_lang == 'en' and target_lang.startswith('zh'):
                # 英译中
                pass
            else:
                raise Exception(f"ModelScope翻译暂不支持 {source_lang} -> {target_lang}，仅支持英译中")
            
            # 尝试不同的API调用格式
            payload = {"input": text}
            result = self._query(payload)
            
            # 处理不同的响应格式
            if 'output' in result:
                return result['output']
            elif 'Data' in result and result['Data']:
                return result['Data'][0].get('translation', text)
            elif 'data' in result:
                return result['data'].get('translation', text)
            elif 'translation' in result:
                return result['translation']
            elif isinstance(result, str):
                return result
            elif result.get('Success') is True:
                # 如果有Success字段且为True，尝试提取翻译结果
                if 'output' in result:
                    return result['output']
                elif 'Data' in result:
                    return result['Data']
            else:
                self.logger.warning(f"未知的API响应格式: {result}")
                raise Exception(f"ModelScope翻译响应格式错误: {result}")
                        
        except Exception as e:
            self.logger.error(f"ModelScope翻译失败: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        return bool(self.sdk_token)
    
    def get_supported_languages(self) -> List[LanguageInfo]:
        return self.supported_languages.copy()




class SimpleTranslateProvider:
    """简单翻译提供者 - 基于规则的翻译（备用方案）"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # 简单的英中词典映射
        self.translation_dict = {
            "hello": "你好",
            "world": "世界",
            "machine": "机器",
            "learning": "学习",
            "artificial": "人工",
            "intelligence": "智能",
            "alibaba": "阿里巴巴",
            "group": "集团",
            "mission": "使命",
            "let": "让",
            "the": "这个",
            "to": "",
            "have": "有",
            "no": "没有",
            "difficult": "困难",
            "business": "生意",
            "weather": "天气",
            "nice": "好的",
            "today": "今天",
            "how": "如何",
            "are": "",
            "you": "你",
            "python": "Python",
            "programming": "编程",
            "code": "代码",
            "software": "软件",
            "development": "开发"
        }
    
    async def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """基于词典的简单翻译"""
        try:
            if source_lang != 'en' or target_lang != 'zh-CN':
                raise Exception("简单翻译仅支持英译中")
            
            # 分词和翻译
            words = text.lower().split()
            translated_words = []
            
            for word in words:
                word_clean = word.strip('.,!?;:"\'')
                translated = self.translation_dict.get(word_clean, word_clean)
                translated_words.append(translated)
            
            result = ' '.join([w for w in translated_words if w])
            self.logger.info(f"简单翻译结果: {text} -> {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"简单翻译失败: {e}")
            raise
    
    def is_available(self) -> bool:
        return True
    
    def get_supported_languages(self) -> List[LanguageInfo]:
        return [
            LanguageInfo("zh-CN", "Chinese (Simplified)", "简体中文"),
            LanguageInfo("en", "English", "English"),
        ]


class TranslationService:
    """翻译服务管理器 - 支持ModelScope和简单翻译"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # 初始化翻译提供者
        self.modelscope_provider = ModelScopeTranslateProvider()
        self.simple_provider = SimpleTranslateProvider()
        
        # 当前活跃的提供者
        self.active_provider = self.modelscope_provider
        
        # 翻译缓存
        self._cache = {}
        self.cache_enabled = self.config.get('cache_enabled', True)
        
        self.logger.info("翻译服务初始化成功")
    
    def _switch_to_simple_provider(self):
        """切换到简单翻译提供者"""
        self.logger.warning("ModelScope翻译服务不可用，切换到简单翻译")
        self.active_provider = self.simple_provider
    
    async def _test_modelscope_provider(self):
        """测试ModelScope提供者是否可用"""
        try:
            await self.modelscope_provider.translate("test", "en", "zh-CN")
            return True
        except Exception as e:
            self.logger.error(f"ModelScope提供者测试失败: {e}")
            return False
    
    async def translate(
        self,
        text: str,
        source_lang: str,
        target_lang: str
    ) -> str:
        """
        翻译文本
        
        Args:
            text: 要翻译的文本
            source_lang: 源语言代码
            target_lang: 目标语言代码
            
        Returns:
            翻译后的文本
        """
        if not text.strip():
            return text
        
        # 检查缓存
        cache_key = f"{hash(text)}_{source_lang}_{target_lang}"
        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]
        
        # 尝试使用活跃的提供者
        try:
            if self.active_provider == self.modelscope_provider:
                # 首先测试ModelScope是否可用
                if await self._test_modelscope_provider():
                    translated_text = await self.active_provider.translate(text, source_lang, target_lang)
                else:
                    self._switch_to_simple_provider()
                    translated_text = await self.active_provider.translate(text, source_lang, target_lang)
            else:
                # 使用简单翻译
                translated_text = await self.active_provider.translate(text, source_lang, target_lang)
            
            # 缓存结果
            if self.cache_enabled:
                self._cache[cache_key] = translated_text
            
            return translated_text
            
        except Exception as e:
            self.logger.error(f"翻译失败: {str(e)}")
            # 如果当前提供者是ModelScope，尝试切换到简单翻译
            if self.active_provider == self.modelscope_provider:
                self._switch_to_simple_provider()
                try:
                    translated_text = await self.active_provider.translate(text, source_lang, target_lang)
                    if self.cache_enabled:
                        self._cache[cache_key] = translated_text
                    return translated_text
                except Exception as e2:
                    self.logger.error(f"简单翻译也失败: {e2}")
                    # 返回原文作为最后手段
                    return text
            else:
                # 返回原文作为最后手段
                return text
    
    
    async def batch_translate(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str
    ) -> List[str]:
        """批量翻译"""
        tasks = [
            self.translate(text, source_lang, target_lang)
            for text in texts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        translated_texts = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"翻译文本 '{texts[i][:50]}...' 失败: {str(result)}")
                translated_texts.append(texts[i])  # 返回原文
            else:
                translated_texts.append(result)
        
        return translated_texts
    
    def get_supported_languages(self) -> List[LanguageInfo]:
        """获取支持的语言列表"""
        return self.provider.get_supported_languages()
    
    def detect_language(self, text: str) -> str:
        """检测文本语言（简单实现）"""
        # 简单的语言检测逻辑
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len(text.replace(' ', ''))
        
        if total_chars == 0:
            return 'en'
        
        chinese_ratio = chinese_chars / total_chars
        
        if chinese_ratio > 0.3:
            return 'zh-CN'
        else:
            return 'en'
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return True  # 总是返回True，因为有备用方案
    
    def get_provider_status(self) -> Dict[str, bool]:
        """获取提供者状态"""
        return {
            "ModelScopeTranslateProvider": self.modelscope_provider.is_available(),
            "SimpleTranslateProvider": self.simple_provider.is_available(),
            "ActiveProvider": self.active_provider.__class__.__name__
        }
    
    def get_active_provider_name(self) -> str:
        """获取当前活跃的提供者名称"""
        return self.active_provider.__class__.__name__
    
    def clear_cache(self):
        """清空翻译缓存"""
        self._cache.clear()
        self.logger.info("翻译缓存已清空")
