"""
智能表情匹配服务
提供多种智能表情匹配方案，包括AI分析、情感分析、语义匹配等
"""

import json
import requests
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import re
from .ai_semantic_analyzer import AISemanticAnalyzer

@dataclass
class EmojiMatch:
    """表情匹配结果"""
    emoji: str
    confidence: float
    reason: str
    category: str

class SmartEmojiMatcher:
    """智能表情匹配器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.semantic_analyzer = AISemanticAnalyzer()
        
        # 情感词典 - 更全面的情感分析
        self.emotion_patterns = {
            # 积极情感
            'joy': {
                'patterns': [r'开心|高兴|快乐|愉快|兴奋|喜悦|满意|舒服', r'happy|joy|excited|pleased|glad|cheerful'],
                'emojis': ['😊', '😄', '😃', '🥳', '😆', '🤗'],
                'weight': 1.0
            },
            'love': {
                'patterns': [r'爱|喜欢|心动|温暖|甜蜜|浪漫', r'love|like|heart|sweet|romantic|warm'],
                'emojis': ['❤️', '💕', '💖', '🥰', '😍', '💝'],
                'weight': 1.0
            },
            'surprise': {
                'patterns': [r'惊讶|震惊|意外|没想到|哇|天哪', r'surprise|shock|wow|amazing|incredible|unbelievable'],
                'emojis': ['😲', '😮', '🤯', '😱', '🙀', '😯'],
                'weight': 0.9
            },
            
            # 消极情感
            'sadness': {
                'patterns': [r'难过|伤心|痛苦|失望|沮丧|郁闷|委屈', r'sad|hurt|disappointed|depressed|upset|miserable'],
                'emojis': ['😢', '😭', '😞', '😔', '💔', '😿'],
                'weight': 1.0
            },
            'anger': {
                'patterns': [r'生气|愤怒|恼火|烦躁|气死|讨厌|烦人', r'angry|mad|furious|annoyed|hate|irritated'],
                'emojis': ['😠', '😡', '🤬', '💢', '😤', '👿'],
                'weight': 1.0
            },
            'fear': {
                'patterns': [r'害怕|恐惧|担心|紧张|焦虑|不安', r'fear|afraid|worried|anxious|nervous|scared'],
                'emojis': ['😨', '😰', '😟', '😧', '🙈', '😬'],
                'weight': 0.8
            },
            
            # 中性情感
            'thinking': {
                'patterns': [r'思考|想|考虑|琢磨|研究|分析', r'think|consider|wonder|analyze|study|research'],
                'emojis': ['🤔', '💭', '🧐', '💡', '🤓', '📝'],
                'weight': 0.7
            },
            'tired': {
                'patterns': [r'累|疲惫|困|睡|休息|懒', r'tired|exhausted|sleepy|lazy|rest|sleep'],
                'emojis': ['😴', '😪', '🥱', '😫', '💤', '🛌'],
                'weight': 0.8
            }
        }
        
        # 主题词典 - 根据内容主题匹配
        self.topic_patterns = {
            'communication': {
                'patterns': [r'电话|通话|聊天|说话|交流|沟通', r'phone|call|chat|talk|communicate|speak'],
                'emojis': ['📞', '☎️', '📱', '💬', '🗣️', '📢'],
                'weight': 1.0
            },
            'family': {
                'patterns': [r'孩子|父母|家人|亲人|家庭|儿子|女儿', r'child|parent|family|son|daughter|kids'],
                'emojis': ['👨‍👩‍👧‍👦', '👪', '👶', '🏠', '💕', '🤱'],
                'weight': 1.0
            },
            'work': {
                'patterns': [r'工作|上班|职场|同事|老板|公司', r'work|job|office|colleague|boss|company'],
                'emojis': ['💼', '🏢', '💻', '📊', '⚡', '🎯'],
                'weight': 0.9
            },
            'study': {
                'patterns': [r'学习|读书|考试|作业|知识|教育', r'study|learn|exam|homework|education|knowledge'],
                'emojis': ['📚', '✏️', '🎓', '📖', '🧠', '💡'],
                'weight': 0.9
            },
            'time': {
                'patterns': [r'时间|钟点|小时|分钟|早上|晚上', r'time|hour|minute|morning|evening|clock'],
                'emojis': ['⏰', '🕐', '⏳', '📅', '🌅', '🌙'],
                'weight': 0.8
            },
            'food': {
                'patterns': [r'吃|食物|饭|菜|饿|美食', r'eat|food|meal|hungry|delicious|restaurant'],
                'emojis': ['🍽️', '🍕', '🍜', '🥘', '😋', '🍴'],
                'weight': 0.8
            },
            'money': {
                'patterns': [r'钱|金钱|花费|便宜|贵|价格', r'money|cost|expensive|cheap|price|pay'],
                'emojis': ['💰', '💸', '💳', '🏦', '💎', '🤑'],
                'weight': 0.8
            }
        }
    
    async def get_smart_emoji(self, text: str, context: Optional[Dict] = None) -> EmojiMatch:
        """
        智能获取表情
        
        Args:
            text: 文本内容
            context: 上下文信息（可选）
            
        Returns:
            EmojiMatch: 匹配结果
        """
        # 方案1: 多层次分析
        emotion_match = self._analyze_emotion(text)
        topic_match = self._analyze_topic(text)
        
        # 方案2: AI语义分析（如果可用）
        ai_match = await self._ai_semantic_analysis(text)
        
        # 综合评分选择最佳匹配
        candidates = [emotion_match, topic_match]
        if ai_match:
            candidates.append(ai_match)
        
        # 选择置信度最高的匹配
        best_match = max(candidates, key=lambda x: x.confidence if x else 0)
        
        if best_match and best_match.confidence > 0.3:
            return best_match
        else:
            # 兜底方案：根据文本长度和语调选择
            return self._fallback_emoji_selection(text)
    
    def _analyze_emotion(self, text: str) -> Optional[EmojiMatch]:
        """情感分析匹配"""
        text_lower = text.lower()
        best_match = None
        max_score = 0
        
        for emotion, config in self.emotion_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in config['patterns']:
                matches = re.findall(pattern, text_lower)
                if matches:
                    score += len(matches) * config['weight']
                    matched_patterns.extend(matches)
            
            if score > max_score:
                max_score = score
                # 随机选择一个该情感类别的表情
                import random
                emoji = random.choice(config['emojis'])
                best_match = EmojiMatch(
                    emoji=emoji,
                    confidence=min(score * 0.3, 1.0),  # 标准化置信度
                    reason=f"情感分析: {emotion}, 匹配词: {matched_patterns[:3]}",
                    category="emotion"
                )
        
        return best_match
    
    def _analyze_topic(self, text: str) -> Optional[EmojiMatch]:
        """主题分析匹配"""
        text_lower = text.lower()
        best_match = None
        max_score = 0
        
        for topic, config in self.topic_patterns.items():
            score = 0
            matched_patterns = []
            
            for pattern in config['patterns']:
                matches = re.findall(pattern, text_lower)
                if matches:
                    score += len(matches) * config['weight']
                    matched_patterns.extend(matches)
            
            if score > max_score:
                max_score = score
                import random
                emoji = random.choice(config['emojis'])
                best_match = EmojiMatch(
                    emoji=emoji,
                    confidence=min(score * 0.4, 1.0),
                    reason=f"主题分析: {topic}, 匹配词: {matched_patterns[:3]}",
                    category="topic"
                )
        
        return best_match
    
    async def _ai_semantic_analysis(self, text: str) -> Optional[EmojiMatch]:
        """AI语义分析（使用ModelScope或其他AI服务）"""
        try:
            analysis = await self.semantic_analyzer.analyze(text)
            # 使用分析结果构建EmojiMatch
            # 优先使用AI建议的emoji，否则根据情感和强度从数据库选择
            db = EmojiDatabase()
            chosen_emoji = analysis.emoji_hint or db.get_emoji_by_emotion_and_intensity(analysis.emotion, analysis.intensity)
            reason = f"AI语义分析: {analysis.reason}; emotion={analysis.emotion}, intensity={analysis.intensity:.2f}, topics={analysis.topics}"
            return EmojiMatch(
                emoji=chosen_emoji,
                confidence=float(analysis.confidence),
                reason=reason,
                category="ai"
            )
        
        except Exception as e:
            self.logger.warning(f"AI语义分析失败: {str(e)}")
            return None
    
    def _fallback_emoji_selection(self, text: str) -> EmojiMatch:
        """兜底表情选择"""
        text_len = len(text)
        
        # 根据文本特征选择
        if '？' in text or '?' in text:
            return EmojiMatch('🤔', 0.5, '疑问句检测', 'fallback')
        elif '！' in text or '!' in text:
            return EmojiMatch('😮', 0.5, '感叹句检测', 'fallback')
        elif text_len > 50:
            return EmojiMatch('📝', 0.4, '长文本', 'fallback')
        else:
            return EmojiMatch('😊', 0.3, '默认表情', 'fallback')
    
    def get_emoji_by_category(self, category: str, subcategory: Optional[str] = None) -> List[str]:
        """根据类别获取表情列表"""
        emoji_categories = {
            'faces': ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇'],
            'emotions': ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔'],
            'gestures': ['👍', '👎', '👌', '🤌', '🤏', '✌️', '🤞', '🤟', '🤘', '🤙'],
            'objects': ['📱', '💻', '⌨️', '🖥️', '🖨️', '📞', '☎️', '📠', '📺', '📻'],
            'activities': ['⚽', '🏀', '🏈', '⚾', '🥎', '🎾', '🏐', '🏉', '🥏', '🎱'],
            'nature': ['🌱', '🌿', '🍀', '🌾', '🌵', '🌲', '🌳', '🌴', '🌸', '🌺']
        }
        
        return emoji_categories.get(category, ['😊'])
    
    def batch_match_emojis(self, texts: List[str]) -> List[EmojiMatch]:
        """批量匹配表情"""
        import asyncio
        
        async def match_all():
            tasks = [self.get_smart_emoji(text) for text in texts]
            return await asyncio.gather(*tasks)
        
        return asyncio.run(match_all())


class EmojiDatabase:
    """表情数据库 - 可扩展的表情管理"""
    
    def __init__(self):
        self.emoji_data = self._load_emoji_database()
    
    def _load_emoji_database(self) -> Dict[str, Any]:
        """加载表情数据库"""
        return {
            'emotions': {
                'positive': {
                    'joy': ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇'],
                    'love': ['😍', '🥰', '😘', '😗', '😙', '😚', '❤️', '🧡', '💛', '💚'],
                    'excitement': ['🤩', '🥳', '🎉', '🎊', '✨', '💫', '⭐', '🌟', '💥', '🔥']
                },
                'negative': {
                    'sadness': ['😢', '😭', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣', '😖'],
                    'anger': ['😠', '😡', '🤬', '💢', '😤', '😾', '👿', '💀', '☠️', '👺'],
                    'fear': ['😨', '😰', '😱', '🙀', '😧', '😦', '😮', '😯', '😲', '🤯']
                },
                'neutral': {
                    'thinking': ['🤔', '💭', '🧐', '🤓', '😐', '😑', '🙄', '😏', '😶', '😪'],
                    'surprise': ['😮', '😯', '😲', '😳', '🤯', '😱', '🙀', '😧', '😦', '🤭']
                }
            },
            'topics': {
                'communication': ['📞', '☎️', '📱', '💬', '🗣️', '📢', '📣', '💭', '🗯️', '💌'],
                'work': ['💼', '🏢', '💻', '📊', '📈', '📉', '⚡', '🎯', '🔧', '⚙️'],
                'family': ['👨‍👩‍👧‍👦', '👪', '👶', '🏠', '💕', '🤱', '👨‍👧', '👩‍👦', '🧸', '🍼'],
                'time': ['⏰', '🕐', '⏳', '📅', '🌅', '🌙', '⏱️', '⏲️', '🕰️', '📆']
            }
        }
    
    def get_emoji_by_emotion_and_intensity(self, emotion: str, intensity: float) -> str:
        """根据情感和强度获取表情"""
        emotion_map = self.emoji_data.get('emotions', {})
        
        if emotion in emotion_map.get('positive', {}):
            emojis = emotion_map['positive'][emotion]
        elif emotion in emotion_map.get('negative', {}):
            emojis = emotion_map['negative'][emotion]
        else:
            emojis = emotion_map.get('neutral', {}).get('thinking', ['🤔'])
        
        # 根据强度选择表情（强度越高选择越靠前的表情）
        index = min(int(intensity * len(emojis)), len(emojis) - 1)
        return emojis[index]


# 使用示例和测试
async def test_smart_emoji_matcher():
    """测试智能表情匹配"""
    matcher = SmartEmojiMatcher()
    
    test_texts = [
        "别总盯着孩子，先过好你自己的日子",
        "是不是又在守着电话，等孩子那半个月才来一次的问候？",
        "一接通，三句话问不出个所以然，就把电话给挂了",
        "然后自己在这边生半天气，觉得养了个白眼狼？",
        "今天工作真的太累了，想要好好休息一下",
        "这个想法真的很棒，我觉得可以试试看！"
    ]
    
    print("🧪 智能表情匹配测试")
    print("=" * 50)
    
    for text in test_texts:
        match = await matcher.get_smart_emoji(text)
        print(f"文本: {text}")
        print(f"表情: {match.emoji}")
        print(f"置信度: {match.confidence:.2f}")
        print(f"理由: {match.reason}")
        print(f"类别: {match.category}")
        print("-" * 30)

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_smart_emoji_matcher())
