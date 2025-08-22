"""表情宇宙数据库 - 超大规模表情数据集"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import random

@dataclass
class EmojiData:
    """表情数据结构"""
    emoji: str
    unicode_name: str
    categories: List[str]
    emotions: List[str]
    intensity: int
    cultural_context: List[str]
    usage_scenarios: List[str]
    frequency_score: float
    sentiment_polarity: float  # -1 to 1
    arousal_level: float      # 0 to 1
    dominance_level: float    # 0 to 1

class EmojiUniverseDB:
    """表情宇宙数据库"""
    
    def __init__(self):
        self.emoji_database = self._build_comprehensive_database()
        self.chinese_cultural_emojis = self._build_chinese_cultural_db()
        self.scenario_based_emojis = self._build_scenario_db()
        self.emotion_intensity_map = self._build_emotion_intensity_map()
    
    def _build_comprehensive_database(self) -> Dict[str, EmojiData]:
        """构建综合表情数据库"""
        emojis = {}
        
        # 基础面部表情 - 喜悦系列
        joy_emojis = [
            ("😀", "grinning_face", 0.9, 0.8, 0.7),
            ("😃", "grinning_face_with_big_eyes", 0.85, 0.75, 0.7),
            ("😄", "grinning_face_with_smiling_eyes", 0.8, 0.7, 0.7),
            ("😁", "beaming_face_with_smiling_eyes", 0.75, 0.7, 0.6),
            ("😆", "grinning_squinting_face", 0.8, 0.8, 0.8),
            ("😅", "grinning_face_with_sweat", 0.6, 0.5, 0.5),
            ("🤣", "rolling_on_the_floor_laughing", 0.95, 0.95, 0.9),
            ("😂", "face_with_tears_of_joy", 0.9, 0.9, 0.8),
            ("🙂", "slightly_smiling_face", 0.4, 0.3, 0.4),
            ("😊", "smiling_face_with_smiling_eyes", 0.7, 0.6, 0.6),
            ("😇", "smiling_face_with_halo", 0.6, 0.5, 0.5),
            ("🥰", "smiling_face_with_hearts", 0.8, 0.7, 0.7),
            ("😍", "smiling_face_with_heart_eyes", 0.8, 0.8, 0.8),
            ("🤩", "star_struck", 0.9, 0.9, 0.9),
            ("😘", "face_blowing_a_kiss", 0.7, 0.6, 0.7)
        ]
        
        for emoji, name, polarity, arousal, dominance in joy_emojis:
            emojis[emoji] = EmojiData(
                emoji=emoji,
                unicode_name=name,
                categories=["face", "emotion"],
                emotions=["joy", "happiness", "positive"],
                intensity=int(arousal * 5),
                cultural_context=["universal"],
                usage_scenarios=["celebration", "happiness", "greeting"],
                frequency_score=0.8,
                sentiment_polarity=polarity,
                arousal_level=arousal,
                dominance_level=dominance
            )
        
        # 悲伤和负面情感系列
        negative_emojis = [
            ("😔", "pensive_face", -0.7, 0.3, 0.2),
            ("😞", "disappointed_face", -0.6, 0.4, 0.3),
            ("😟", "worried_face", -0.5, 0.6, 0.3),
            ("😕", "confused_face", -0.3, 0.4, 0.3),
            ("🙁", "slightly_frowning_face", -0.4, 0.3, 0.3),
            ("☹️", "frowning_face", -0.5, 0.4, 0.3),
            ("😣", "persevering_face", -0.6, 0.7, 0.4),
            ("😖", "confounded_face", -0.7, 0.8, 0.3),
            ("😫", "tired_face", -0.8, 0.6, 0.2),
            ("😩", "weary_face", -0.8, 0.5, 0.2),
            ("😢", "crying_face", -0.8, 0.7, 0.2),
            ("😭", "loudly_crying_face", -0.9, 0.9, 0.3),
            ("😠", "angry_face", -0.7, 0.8, 0.8),
            ("😡", "pouting_face", -0.8, 0.9, 0.9),
            ("🤬", "face_with_symbols_on_mouth", -0.9, 0.95, 0.9)
        ]
        
        for emoji, name, polarity, arousal, dominance in negative_emojis:
            emotion_type = "sadness" if polarity < -0.5 and arousal < 0.7 else "anger" if arousal > 0.7 else "fear"
            emojis[emoji] = EmojiData(
                emoji=emoji,
                unicode_name=name,
                categories=["face", "emotion"],
                emotions=[emotion_type, "negative"],
                intensity=int(abs(polarity) * 5),
                cultural_context=["universal"],
                usage_scenarios=["disappointment", "sadness", "frustration"],
                frequency_score=0.6,
                sentiment_polarity=polarity,
                arousal_level=arousal,
                dominance_level=dominance
            )
        
        # 思考和中性表情
        thinking_emojis = [
            ("🤔", "thinking_face", 0.0, 0.5, 0.6),
            ("🤨", "face_with_raised_eyebrow", -0.1, 0.4, 0.7),
            ("🧐", "face_with_monocle", 0.1, 0.4, 0.8),
            ("🤓", "nerd_face", 0.3, 0.3, 0.7),
            ("😐", "neutral_face", 0.0, 0.2, 0.5),
            ("😑", "expressionless_face", -0.1, 0.1, 0.4),
            ("🙄", "face_with_rolling_eyes", -0.3, 0.4, 0.6),
            ("😏", "smirking_face", 0.2, 0.4, 0.7),
            ("😒", "unamused_face", -0.4, 0.3, 0.5)
        ]
        
        for emoji, name, polarity, arousal, dominance in thinking_emojis:
            emojis[emoji] = EmojiData(
                emoji=emoji,
                unicode_name=name,
                categories=["face", "emotion"],
                emotions=["thinking", "contemplation", "neutral"],
                intensity=int(arousal * 5),
                cultural_context=["universal"],
                usage_scenarios=["thinking", "contemplation", "boredom"],
                frequency_score=0.7,
                sentiment_polarity=polarity,
                arousal_level=arousal,
                dominance_level=dominance
            )
        
        return emojis
    
    def _build_chinese_cultural_db(self) -> Dict[str, List[EmojiData]]:
        """构建中文文化特色表情数据库"""
        return {
            "face_culture": [
                EmojiData("😅", "grinning_face_with_sweat", ["face"], ["embarrassment"], 3, 
                         ["chinese"], ["saving_face"], 0.8, 0.2, 0.4, 0.3),
                EmojiData("😬", "grimacing_face", ["face"], ["awkwardness"], 4,
                         ["chinese"], ["uncomfortable_situation"], 0.7, -0.3, 0.6, 0.4),
                EmojiData("🤭", "face_with_hand_over_mouth", ["face"], ["surprise"], 2,
                         ["chinese"], ["modest_reaction"], 0.6, 0.3, 0.4, 0.3)
            ],
            "filial_piety": [
                EmojiData("🙏", "folded_hands", ["gesture"], ["respect"], 3,
                         ["chinese"], ["respect", "gratitude"], 0.9, 0.6, 0.3, 0.4),
                EmojiData("😇", "smiling_face_with_halo", ["face"], ["virtue"], 2,
                         ["universal"], ["good_behavior"], 0.5, 0.7, 0.5, 0.5),
                EmojiData("💝", "heart_with_ribbon", ["heart"], ["love"], 4,
                         ["universal"], ["family_love"], 0.7, 0.8, 0.6, 0.6)
            ]
        }
    
    def _build_scenario_db(self) -> Dict[str, Dict[str, List[EmojiData]]]:
        """构建场景化表情数据库"""
        return {
            "family_scenarios": {
                "parent_child_communication": [
                    EmojiData("📞", "telephone", ["object"], ["communication"], 2, ["universal"], 
                             ["phone_call"], 0.8, 0.0, 0.4, 0.5),
                    EmojiData("💬", "speech_balloon", ["symbol"], ["conversation"], 2, ["universal"],
                             ["chat"], 0.9, 0.1, 0.4, 0.5),
                    EmojiData("👨‍👧", "man_and_girl", ["people"], ["family"], 3, ["universal"],
                             ["father_daughter"], 0.6, 0.7, 0.5, 0.6)
                ],
                "generational_conflict": [
                    EmojiData("🙄", "face_with_rolling_eyes", ["face"], ["annoyance"], 3, ["universal"],
                             ["eye_roll"], 0.8, -0.3, 0.4, 0.6),
                    EmojiData("😤", "face_with_steam_from_nose", ["face"], ["frustration"], 4, ["universal"],
                             ["frustration"], 0.7, -0.3, 0.8, 0.7),
                    EmojiData("🤷‍♂️", "man_shrugging", ["people"], ["indifference"], 2, ["universal"],
                             ["shrug"], 0.8, 0.0, 0.3, 0.4)
                ]
            }
        }
    
    def _build_emotion_intensity_map(self) -> Dict[str, Dict[int, List[str]]]:
        """构建情感强度映射"""
        return {
            "joy": {
                1: ["🙂", "☺️", "😌"],
                2: ["😊", "😇", "🙃"],
                3: ["😄", "😃", "😀", "🤗"],
                4: ["😆", "😁", "🥰", "😍"],
                5: ["🤣", "😂", "🤩", "🥳"]
            },
            "sadness": {
                1: ["🙁", "😕", "☹️"],
                2: ["😔", "😞", "😟"],
                3: ["😣", "😖", "😥"],
                4: ["😫", "😩", "😢"],
                5: ["😭", "💔", "😿"]
            },
            "anger": {
                1: ["😐", "😑", "😒"],
                2: ["🙄", "😤", "🤨"],
                3: ["😠", "😾", "💢"],
                4: ["😡", "👿", "🔥"],
                5: ["🤬", "👹", "💥"]
            },
            "thinking": {
                1: ["😐", "😶", "🤐"],
                2: ["🤔", "💭", "🙄"],
                3: ["🧐", "🤓", "📝"],
                4: ["💡", "🧠", "⚡"],
                5: ["🌟", "✨", "💫"]
            }
        }
    
    def get_emojis_by_emotion_and_intensity(self, emotion: str, intensity: int) -> List[str]:
        """根据情感和强度获取表情列表"""
        intensity = max(1, min(5, intensity))
        return self.emotion_intensity_map.get(emotion, {}).get(intensity, ["😊"])
    
    def get_emojis_by_scenario(self, scenario: str, sub_scenario: Optional[str] = None) -> List[EmojiData]:
        """根据场景获取表情"""
        if scenario in self.scenario_based_emojis:
            if sub_scenario and sub_scenario in self.scenario_based_emojis[scenario]:
                return self.scenario_based_emojis[scenario][sub_scenario]
            else:
                all_emojis = []
                for sub_dict in self.scenario_based_emojis[scenario].values():
                    all_emojis.extend(sub_dict)
                return all_emojis
        return []
    
    def get_cultural_emojis(self, culture: str) -> List[EmojiData]:
        """获取特定文化的表情"""
        return self.chinese_cultural_emojis.get(culture, [])
    
    def get_random_emoji_by_criteria(self, emotion: Optional[str] = None, 
                                   intensity: Optional[int] = None) -> str:
        """根据条件随机获取表情"""
        candidates = []
        
        for emoji_data in self.emoji_database.values():
            match = True
            
            if emotion and emotion not in emoji_data.emotions:
                match = False
            
            if intensity and abs(emoji_data.intensity - intensity) > 1:
                match = False
            
            if match:
                candidates.append(emoji_data.emoji)
        
        return random.choice(candidates) if candidates else "😊"

if __name__ == "__main__":
    db = EmojiUniverseDB()
    print("表情数据库已加载")
    print(f"总表情数: {len(db.emoji_database)}")
    print(f"文化表情类别: {len(db.chinese_cultural_emojis)}")
    print(f"场景类别: {len(db.scenario_based_emojis)}")
