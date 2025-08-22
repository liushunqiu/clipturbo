"""
AI表情生成器 - 使用AI模型动态生成最合适的表情
支持多种AI服务，包括本地模型和云端API
"""

import json
import requests
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import asyncio

@dataclass
class AIEmojiResult:
    """AI表情生成结果"""
    emoji: str
    confidence: float
    reasoning: str
    alternatives: List[str]
    emotion_analysis: Dict[str, float]

class AIEmojiGenerator:
    """AI驱动的表情生成器"""
    
    def __init__(self, modelscope_token: str = "ms-c0d318a3-9811-4fac-8f4a-353383a30edd"):
        self.modelscope_token = modelscope_token
        self.logger = logging.getLogger(__name__)
        
        # 表情数据库
        self.emoji_database = {
            'emotions': {
                'joy': ['😊', '😄', '😃', '🥳', '😆', '🤗', '😁', '😂'],
                'love': ['❤️', '💕', '💖', '🥰', '😍', '💝', '💗', '💘'],
                'surprise': ['😲', '😮', '🤯', '😱', '🙀', '😯', '🤭', '😳'],
                'sadness': ['😢', '😭', '😞', '😔', '💔', '😿', '😪', '😫'],
                'anger': ['😠', '😡', '🤬', '💢', '😤', '👿', '😾', '🔥'],
                'fear': ['😨', '😰', '😟', '😧', '🙈', '😬', '😱', '🫣'],
                'thinking': ['🤔', '💭', '🧐', '💡', '🤓', '📝', '🤯', '💫'],
                'tired': ['😴', '😪', '🥱', '😫', '💤', '🛌', '😵‍💫', '🫠']
            },
            'objects': {
                'communication': ['📞', '☎️', '📱', '💬', '🗣️', '📢', '📣', '💌'],
                'family': ['👨‍👩‍👧‍👦', '👪', '👶', '🏠', '💕', '🤱', '👨‍👧', '👩‍👦'],
                'work': ['💼', '🏢', '💻', '📊', '📈', '⚡', '🎯', '🔧'],
                'time': ['⏰', '🕐', '⏳', '📅', '🌅', '🌙', '⏱️', '📆'],
                'food': ['🍽️', '🍕', '🍜', '🥘', '😋', '🍴', '🥢', '🍲'],
                'nature': ['🌱', '🌸', '🌺', '🌻', '🌷', '🌹', '🌿', '🍀'],
                'animals': ['🐕', '🐱', '🐦', '🦋', '🐝', '🐠', '🐰', '🐼']
            }
        }
    
    async def generate_emoji_with_ai(self, text: str, context: Optional[Dict] = None) -> AIEmojiResult:
        """
        使用AI生成最合适的表情
        
        Args:
            text: 文本内容
            context: 上下文信息
            
        Returns:
            AIEmojiResult: AI生成的表情结果
        """
        try:
            # 方案1: 使用ModelScope的情感分析 + 自定义逻辑
            emotion_analysis = await self._analyze_emotion_with_ai(text)
            
            # 方案2: 使用prompt engineering让AI直接推荐表情
            ai_recommendation = await self._get_ai_emoji_recommendation(text, context)
            
            # 综合分析结果
            return self._combine_ai_results(text, emotion_analysis, ai_recommendation)
            
        except Exception as e:
            self.logger.error(f"AI表情生成失败: {str(e)}")
            return self._fallback_emoji_generation(text)
    
    async def _analyze_emotion_with_ai(self, text: str) -> Dict[str, float]:
        """使用AI进行情感分析"""
        try:
            # 构造情感分析prompt
            prompt = f"""
            请分析以下文本的情感成分，给出各种情感的强度评分（0-1之间）：
            
            文本："{text}"
            
            请返回JSON格式，包含以下情感维度：
            - joy（快乐）
            - sadness（悲伤）
            - anger（愤怒）
            - fear（恐惧）
            - surprise（惊讶）
            - love（爱意）
            - thinking（思考）
            - tired（疲惫）
            
            示例格式：{{"joy": 0.8, "sadness": 0.1, "anger": 0.0, ...}}
            """
            
            # 这里可以调用ModelScope的文本分析API
            # 暂时使用简单的规则分析
            return self._simple_emotion_analysis(text)
            
        except Exception as e:
            self.logger.warning(f"AI情感分析失败: {str(e)}")
            return self._simple_emotion_analysis(text)
    
    async def _get_ai_emoji_recommendation(self, text: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """获取AI的表情推荐"""
        try:
            # 构造表情推荐prompt
            context_info = ""
            if context:
                context_info = f"上下文信息：{json.dumps(context, ensure_ascii=False)}\n"
            
            prompt = f"""
            作为一个表情推荐专家，请为以下文本推荐最合适的emoji表情：
            
            {context_info}文本："{text}"
            
            请考虑：
            1. 文本的情感色彩
            2. 主要话题和内容
            3. 语言风格和语调
            4. 文化背景和使用场景
            
            请返回JSON格式：
            {{
                "primary_emoji": "主要推荐的emoji",
                "confidence": 0.85,
                "reasoning": "推荐理由",
                "alternatives": ["备选emoji1", "备选emoji2", "备选emoji3"],
                "category": "情感类别或主题类别"
            }}
            """
            
            # 这里可以调用更强大的AI模型
            # 暂时返回基于规则的推荐
            return self._rule_based_recommendation(text)
            
        except Exception as e:
            self.logger.warning(f"AI表情推荐失败: {str(e)}")
            return self._rule_based_recommendation(text)
    
    def _simple_emotion_analysis(self, text: str) -> Dict[str, float]:
        """简单的情感分析"""
        emotions = {
            'joy': 0.0, 'sadness': 0.0, 'anger': 0.0, 'fear': 0.0,
            'surprise': 0.0, 'love': 0.0, 'thinking': 0.0, 'tired': 0.0
        }
        
        text_lower = text.lower()
        
        # 积极情感词汇
        joy_words = ['开心', '高兴', '快乐', '愉快', '兴奋', 'happy', 'joy', 'excited', 'glad']
        love_words = ['爱', '喜欢', '心动', '温暖', 'love', 'like', 'heart', 'warm']
        
        # 消极情感词汇
        sad_words = ['难过', '伤心', '痛苦', '失望', 'sad', 'hurt', 'disappointed', 'upset']
        angry_words = ['生气', '愤怒', '恼火', '烦躁', 'angry', 'mad', 'furious', 'annoyed']
        
        # 其他情感词汇
        surprise_words = ['惊讶', '震惊', '意外', '哇', 'surprise', 'shock', 'wow', 'amazing']
        thinking_words = ['思考', '想', '考虑', 'think', 'consider', 'wonder']
        tired_words = ['累', '疲惫', '困', 'tired', 'exhausted', 'sleepy']
        
        # 计算情感强度
        for word in joy_words:
            if word in text_lower:
                emotions['joy'] += 0.3
        
        for word in love_words:
            if word in text_lower:
                emotions['love'] += 0.3
        
        for word in sad_words:
            if word in text_lower:
                emotions['sadness'] += 0.3
        
        for word in angry_words:
            if word in text_lower:
                emotions['anger'] += 0.3
        
        for word in surprise_words:
            if word in text_lower:
                emotions['surprise'] += 0.3
        
        for word in thinking_words:
            if word in text_lower:
                emotions['thinking'] += 0.2
        
        for word in tired_words:
            if word in text_lower:
                emotions['tired'] += 0.2
        
        # 标准化到0-1范围
        for emotion in emotions:
            emotions[emotion] = min(emotions[emotion], 1.0)
        
        return emotions
    
    def _rule_based_recommendation(self, text: str) -> Dict[str, Any]:
        """基于规则的表情推荐"""
        text_lower = text.lower()
        
        # 主题检测
        if any(word in text_lower for word in ['电话', '通话', '打电话', 'phone', 'call']):
            return {
                'primary_emoji': '📞',
                'confidence': 0.8,
                'reasoning': '检测到通讯相关内容',
                'alternatives': ['☎️', '📱', '💬'],
                'category': 'communication'
            }
        
        if any(word in text_lower for word in ['孩子', '父母', '家人', 'child', 'parent', 'family']):
            return {
                'primary_emoji': '👪',
                'confidence': 0.8,
                'reasoning': '检测到家庭相关内容',
                'alternatives': ['👨‍👩‍👧‍👦', '💕', '🏠'],
                'category': 'family'
            }
        
        # 情感检测
        if any(word in text_lower for word in ['生气', '愤怒', '恼火', 'angry', 'mad']):
            return {
                'primary_emoji': '😠',
                'confidence': 0.9,
                'reasoning': '检测到愤怒情感',
                'alternatives': ['😡', '🤬', '💢'],
                'category': 'anger'
            }
        
        if any(word in text_lower for word in ['难过', '伤心', 'sad', 'hurt']):
            return {
                'primary_emoji': '😢',
                'confidence': 0.9,
                'reasoning': '检测到悲伤情感',
                'alternatives': ['😭', '😞', '💔'],
                'category': 'sadness'
            }
        
        # 默认推荐
        return {
            'primary_emoji': '😊',
            'confidence': 0.5,
            'reasoning': '默认友好表情',
            'alternatives': ['🙂', '😌', '😐'],
            'category': 'neutral'
        }
    
    def _combine_ai_results(self, text: str, emotion_analysis: Dict[str, float], 
                           ai_recommendation: Dict[str, Any]) -> AIEmojiResult:
        """综合AI分析结果"""
        
        # 找出最强的情感
        dominant_emotion = max(emotion_analysis, key=emotion_analysis.get)
        emotion_strength = emotion_analysis[dominant_emotion]
        
        # 如果情感强度很高，优先使用情感表情
        if emotion_strength > 0.6:
            emoji_candidates = self.emoji_database['emotions'].get(dominant_emotion, ['😊'])
            primary_emoji = emoji_candidates[0]
            confidence = emotion_strength * 0.9
            reasoning = f"强烈的{dominant_emotion}情感 (强度: {emotion_strength:.2f})"
        else:
            # 否则使用AI推荐的表情
            primary_emoji = ai_recommendation['primary_emoji']
            confidence = ai_recommendation['confidence']
            reasoning = ai_recommendation['reasoning']
        
        return AIEmojiResult(
            emoji=primary_emoji,
            confidence=confidence,
            reasoning=reasoning,
            alternatives=ai_recommendation.get('alternatives', []),
            emotion_analysis=emotion_analysis
        )
    
    def _fallback_emoji_generation(self, text: str) -> AIEmojiResult:
        """兜底表情生成"""
        if '？' in text or '?' in text:
            emoji = '🤔'
            reasoning = '疑问句检测'
        elif '！' in text or '!' in text:
            emoji = '😮'
            reasoning = '感叹句检测'
        else:
            emoji = '😊'
            reasoning = '默认友好表情'
        
        return AIEmojiResult(
            emoji=emoji,
            confidence=0.4,
            reasoning=reasoning,
            alternatives=['🙂', '😌', '😐'],
            emotion_analysis={}
        )
    
    async def batch_generate_emojis(self, texts: List[str]) -> List[AIEmojiResult]:
        """批量生成表情"""
        tasks = [self.generate_emoji_with_ai(text) for text in texts]
        return await asyncio.gather(*tasks)
    
    def get_emoji_explanation(self, emoji: str) -> Dict[str, Any]:
        """获取表情的含义解释"""
        emoji_meanings = {
            '😊': {'meaning': '友好微笑', 'usage': '表达友善、满意、轻松的心情'},
            '😢': {'meaning': '流泪', 'usage': '表达悲伤、失望、感动的情感'},
            '😠': {'meaning': '愤怒', 'usage': '表达生气、不满、恼火的情绪'},
            '🤔': {'meaning': '思考', 'usage': '表达思考、疑问、考虑的状态'},
            '📞': {'meaning': '电话', 'usage': '表示通讯、联系、电话相关内容'},
            '👪': {'meaning': '家庭', 'usage': '表示家人、亲情、家庭相关话题'}
        }
        
        return emoji_meanings.get(emoji, {
            'meaning': '表情符号',
            'usage': '用于表达情感或补充文字内容'
        })


# 测试和使用示例
async def test_ai_emoji_generator():
    """测试AI表情生成器"""
    generator = AIEmojiGenerator()
    
    test_texts = [
        "别总盯着孩子，先过好你自己的日子",
        "是不是又在守着电话，等孩子那半个月才来一次的问候？",
        "一接通，三句话问不出个所以然，就把电话给挂了",
        "然后自己在这边生半天气，觉得养了个白眼狼？",
        "今天的天气真不错，心情也变好了！",
        "这个问题我需要仔细想想..."
    ]
    
    print("🤖 AI表情生成器测试")
    print("=" * 60)
    
    for text in test_texts:
        result = await generator.generate_emoji_with_ai(text)
        
        print(f"📝 文本: {text}")
        print(f"🎭 表情: {result.emoji}")
        print(f"📊 置信度: {result.confidence:.2f}")
        print(f"💡 推理: {result.reasoning}")
        print(f"🔄 备选: {' '.join(result.alternatives)}")
        
        if result.emotion_analysis:
            top_emotions = sorted(result.emotion_analysis.items(), 
                                key=lambda x: x[1], reverse=True)[:3]
            print(f"😊 情感分析: {', '.join([f'{e}({s:.2f})' for e, s in top_emotions])}")
        
        print("-" * 50)

if __name__ == "__main__":
    asyncio.run(test_ai_emoji_generator())
