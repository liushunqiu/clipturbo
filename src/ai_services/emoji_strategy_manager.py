"""
表情匹配策略管理器
支持多种表情匹配策略，用户可以根据需求选择最合适的方案
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from enum import Enum
from dataclasses import dataclass

from .smart_emoji_matcher import SmartEmojiMatcher, EmojiMatch
from .ai_emoji_generator import AIEmojiGenerator, AIEmojiResult

class EmojiStrategy(Enum):
    """表情匹配策略枚举"""
    SMART_RULE = "smart_rule"          # 智能规则匹配
    AI_ENHANCED = "ai_enhanced"        # AI增强匹配
    HYBRID = "hybrid"                  # 混合策略
    USER_DEFINED = "user_defined"      # 用户自定义
    RANDOM_THEMED = "random_themed"    # 主题随机

@dataclass
class EmojiStrategyConfig:
    """表情策略配置"""
    strategy: EmojiStrategy
    confidence_threshold: float = 0.5
    fallback_strategy: Optional[EmojiStrategy] = None
    custom_mappings: Optional[Dict[str, str]] = None
    theme_preference: Optional[str] = None  # 'cute', 'professional', 'expressive'

class EmojiStrategyManager:
    """表情策略管理器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.smart_matcher = SmartEmojiMatcher()
        self.ai_generator = AIEmojiGenerator()
        
        # 主题表情库
        self.themed_emojis = {
            'cute': {
                'positive': ['🥰', '😊', '🤗', '😋', '🥳', '😸', '🐱', '🌸'],
                'negative': ['😿', '🥺', '😔', '😪', '🙈', '💔', '🌧️', '🍂'],
                'neutral': ['🤔', '😌', '🙂', '😐', '🤷‍♀️', '📝', '💭', '⭐']
            },
            'professional': {
                'positive': ['👍', '✅', '💡', '🎯', '📈', '⚡', '🔥', '💪'],
                'negative': ['❌', '⚠️', '📉', '🔴', '💢', '⛔', '🚫', '❗'],
                'neutral': ['📊', '📋', '🔍', '⚙️', '📌', '💼', '🏢', '📝']
            },
            'expressive': {
                'positive': ['🤩', '😍', '🥳', '🎉', '🔥', '💥', '✨', '🌟'],
                'negative': ['😭', '😡', '🤬', '💀', '👿', '💔', '⚡', '🌪️'],
                'neutral': ['🤯', '😱', '🙄', '🤷', '🤦', '💭', '🧠', '🎭']
            }
        }
    
    async def get_emoji_by_strategy(self, text: str, config: EmojiStrategyConfig, 
                                   context: Optional[Dict] = None) -> Union[EmojiMatch, AIEmojiResult, str]:
        """根据策略获取表情"""
        
        try:
            if config.strategy == EmojiStrategy.SMART_RULE:
                return await self._smart_rule_strategy(text, config)
            
            elif config.strategy == EmojiStrategy.AI_ENHANCED:
                return await self._ai_enhanced_strategy(text, config, context)
            
            elif config.strategy == EmojiStrategy.HYBRID:
                return await self._hybrid_strategy(text, config, context)
            
            elif config.strategy == EmojiStrategy.USER_DEFINED:
                return self._user_defined_strategy(text, config)
            
            elif config.strategy == EmojiStrategy.RANDOM_THEMED:
                return self._random_themed_strategy(text, config)
            
            else:
                # 默认使用智能规则
                return await self._smart_rule_strategy(text, config)
                
        except Exception as e:
            self.logger.error(f"表情策略执行失败: {str(e)}")
            return await self._fallback_strategy(text, config)
    
    async def _smart_rule_strategy(self, text: str, config: EmojiStrategyConfig) -> EmojiMatch:
        """智能规则策略"""
        match = await self.smart_matcher.get_smart_emoji(text)
        
        if match.confidence < config.confidence_threshold:
            if config.fallback_strategy:
                return await self.get_emoji_by_strategy(
                    text, 
                    EmojiStrategyConfig(strategy=config.fallback_strategy)
                )
        
        return match
    
    async def _ai_enhanced_strategy(self, text: str, config: EmojiStrategyConfig, 
                                   context: Optional[Dict] = None) -> AIEmojiResult:
        """AI增强策略"""
        result = await self.ai_generator.generate_emoji_with_ai(text, context)
        
        if result.confidence < config.confidence_threshold:
            if config.fallback_strategy:
                return await self.get_emoji_by_strategy(
                    text,
                    EmojiStrategyConfig(strategy=config.fallback_strategy)
                )
        
        return result
    
    async def _hybrid_strategy(self, text: str, config: EmojiStrategyConfig, 
                              context: Optional[Dict] = None) -> Union[EmojiMatch, AIEmojiResult]:
        """混合策略 - 结合多种方法"""
        
        # 并行执行多种策略
        smart_task = self.smart_matcher.get_smart_emoji(text)
        ai_task = self.ai_generator.generate_emoji_with_ai(text, context)
        
        smart_result, ai_result = await asyncio.gather(smart_task, ai_task)
        
        # 选择置信度更高的结果
        if smart_result.confidence > ai_result.confidence:
            return smart_result
        else:
            return ai_result
    
    def _user_defined_strategy(self, text: str, config: EmojiStrategyConfig) -> str:
        """用户自定义策略"""
        if not config.custom_mappings:
            return '😊'  # 默认表情
        
        text_lower = text.lower()
        
        # 查找用户定义的映射
        for keyword, emoji in config.custom_mappings.items():
            if keyword.lower() in text_lower:
                return emoji
        
        # 没有匹配时返回默认表情
        return '😊'
    
    def _random_themed_strategy(self, text: str, config: EmojiStrategyConfig) -> str:
        """主题随机策略"""
        import random
        
        theme = config.theme_preference or 'cute'
        theme_emojis = self.themed_emojis.get(theme, self.themed_emojis['cute'])
        
        # 简单情感检测
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['开心', '高兴', '好', 'happy', 'good', 'great']):
            return random.choice(theme_emojis['positive'])
        elif any(word in text_lower for word in ['难过', '生气', '不好', 'sad', 'angry', 'bad']):
            return random.choice(theme_emojis['negative'])
        else:
            return random.choice(theme_emojis['neutral'])
    
    async def _fallback_strategy(self, text: str, config: EmojiStrategyConfig) -> str:
        """兜底策略"""
        # 最简单的兜底逻辑
        if '？' in text or '?' in text:
            return '🤔'
        elif '！' in text or '!' in text:
            return '😮'
        else:
            return '😊'
    
    def create_strategy_config(self, strategy_name: str, **kwargs) -> EmojiStrategyConfig:
        """创建策略配置的便捷方法"""
        
        presets = {
            'default': EmojiStrategyConfig(
                strategy=EmojiStrategy.SMART_RULE,
                confidence_threshold=0.5,
                fallback_strategy=EmojiStrategy.RANDOM_THEMED
            ),
            'ai_powered': EmojiStrategyConfig(
                strategy=EmojiStrategy.AI_ENHANCED,
                confidence_threshold=0.6,
                fallback_strategy=EmojiStrategy.SMART_RULE
            ),
            'balanced': EmojiStrategyConfig(
                strategy=EmojiStrategy.HYBRID,
                confidence_threshold=0.5
            ),
            'cute_style': EmojiStrategyConfig(
                strategy=EmojiStrategy.RANDOM_THEMED,
                theme_preference='cute'
            ),
            'professional': EmojiStrategyConfig(
                strategy=EmojiStrategy.RANDOM_THEMED,
                theme_preference='professional'
            ),
            'expressive': EmojiStrategyConfig(
                strategy=EmojiStrategy.RANDOM_THEMED,
                theme_preference='expressive'
            )
        }
        
        if strategy_name in presets:
            config = presets[strategy_name]
            # 应用用户自定义参数
            for key, value in kwargs.items():
                if hasattr(config, key):
                    setattr(config, key, value)
            return config
        else:
            # 创建自定义配置
            return EmojiStrategyConfig(
                strategy=EmojiStrategy.SMART_RULE,
                **kwargs
            )
    
    async def batch_process_with_strategy(self, texts: List[str], 
                                         config: EmojiStrategyConfig) -> List[str]:
        """批量处理文本，返回表情列表"""
        tasks = [self.get_emoji_by_strategy(text, config) for text in texts]
        results = await asyncio.gather(*tasks)
        
        # 提取表情字符串
        emojis = []
        for result in results:
            if isinstance(result, str):
                emojis.append(result)
            elif hasattr(result, 'emoji'):
                emojis.append(result.emoji)
            else:
                emojis.append('😊')  # 兜底
        
        return emojis
    
    def get_available_strategies(self) -> Dict[str, str]:
        """获取可用的策略列表"""
        return {
            'smart_rule': '智能规则匹配 - 基于情感和主题的规则匹配',
            'ai_enhanced': 'AI增强匹配 - 使用AI模型进行语义分析',
            'hybrid': '混合策略 - 结合多种方法选择最佳结果',
            'user_defined': '用户自定义 - 使用用户提供的关键词映射',
            'random_themed': '主题随机 - 根据主题随机选择表情'
        }
    
    def get_theme_options(self) -> Dict[str, List[str]]:
        """获取主题选项"""
        return {
            'cute': ['可爱风格', '适合轻松愉快的内容'],
            'professional': ['专业风格', '适合商务和工作场景'],
            'expressive': ['表现力强', '适合情感丰富的内容']
        }


# 使用示例
async def demo_emoji_strategies():
    """演示不同的表情策略"""
    manager = EmojiStrategyManager()
    
    test_text = "别总盯着孩子，先过好你自己的日子"
    
    print("🎭 表情策略演示")
    print("=" * 50)
    print(f"测试文本: {test_text}\n")
    
    # 测试不同策略
    strategies = [
        ('default', '默认策略'),
        ('ai_powered', 'AI驱动'),
        ('balanced', '平衡策略'),
        ('cute_style', '可爱风格'),
        ('professional', '专业风格'),
        ('expressive', '表现力强')
    ]
    
    for strategy_name, description in strategies:
        config = manager.create_strategy_config(strategy_name)
        result = await manager.get_emoji_by_strategy(test_text, config)
        
        if isinstance(result, str):
            emoji = result
            info = "主题匹配"
        else:
            emoji = result.emoji
            confidence = getattr(result, 'confidence', 0)
            info = f"置信度: {confidence:.2f}"
        
        print(f"{description:12} | {emoji} | {info}")
    
    print("\n" + "=" * 50)
    
    # 演示用户自定义映射
    custom_config = EmojiStrategyConfig(
        strategy=EmojiStrategy.USER_DEFINED,
        custom_mappings={
            '孩子': '👶',
            '电话': '📞',
            '生气': '😠',
            '日子': '📅'
        }
    )
    
    custom_result = await manager.get_emoji_by_strategy(test_text, custom_config)
    print(f"用户自定义映射: {custom_result}")

if __name__ == "__main__":
    asyncio.run(demo_emoji_strategies())
