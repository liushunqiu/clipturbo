"""
AI Semantic Analyzer for Chinese text with cultural and emotional nuances.
- Combines lightweight rule-based analysis and optional external AI (ModelScope) enrichment.
- Async API for batch usage.
"""

from __future__ import annotations

import os
import re
import json
import asyncio
import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

try:
    import aiohttp  # optional for external AI
except Exception:  # pragma: no cover
    aiohttp = None


logger = logging.getLogger(__name__)


@dataclass
class SemanticAnalysis:
    emotion: str
    intensity: float
    topics: List[str]
    emoji_hint: Optional[str]
    confidence: float
    reason: str


class AISemanticAnalyzer:
    """
    Hybrid semantic analyzer:
    1) Fast lexical/cultural rules for robust baseline.
    2) Optional ModelScope API enrichment (if MODELSCOPE_TOKEN present and aiohttp available).
    """

    def __init__(self, modelscope_endpoint: Optional[str] = None, token: Optional[str] = None):
        self.token = token or os.getenv("MODELSCOPE_TOKEN")
        self.modelscope_endpoint = modelscope_endpoint or os.getenv(
            "MODELSCOPE_TEXT_CLASSIFIER_URL", ""
        )

        # Emotion lexicon (Chinese + English) with weights
        self.lexicon: Dict[str, Dict[str, Any]] = {
            "joy": {"patterns": [r"开心|高兴|快乐|愉快|兴奋|满意|舒服|棒|赞|不错|给力|可以|很棒", r"happy|joy|excited|glad|cheerful|great|awesome|nice|good"], "base": 0.7},
            "love": {"patterns": [r"爱|喜欢|心动|温暖|甜蜜|浪漫", r"love|like|heart|sweet|romantic"], "base": 0.7},
            "surprise": {"patterns": [r"惊讶|震惊|意外|哇|天哪", r"surprise|shock|wow|amazing"], "base": 0.6},
            "sadness": {"patterns": [r"难过|伤心|痛苦|失望|沮丧|郁闷|委屈", r"sad|disappointed|depressed|upset"], "base": 0.8},
            "anger": {"patterns": [r"生气|生.*气|愤怒|恼火|烦躁|气死|讨厌", r"angry|furious|annoyed|hate"], "base": 0.8},
            "fear": {"patterns": [r"害怕|恐惧|担心|紧张|焦虑|不安", r"fear|afraid|worried|anxious|nervous"], "base": 0.6},
            "tired": {"patterns": [r"累|疲惫|困|困倦|劳累|疲劳", r"tired|exhausted|sleepy|fatigued"], "base": 0.7},
            "thinking": {"patterns": [r"思考|考虑|琢磨|研究|分析", r"think|consider|analyze|study"], "base": 0.5},
        }

        # Intensity modifiers and negations
        self.intensifiers = [r"非常|特别|超级|太|极其|爆|很|so|very|super|extremely"]
        self.diminishers = [r"有点|有些|稍微|还好|还行|just|a bit|slightly|somewhat"]
        self.negations = [r"不|没|别|无|never|not|no"]

        # Topic patterns (for emoji hinting)
        self.topic_patterns = {
            "communication": [r"电话|通话|聊天|说话|沟通", r"phone|call|chat|talk"],
            "family": [r"孩子|父母|家人|亲人|家庭", r"child|parent|family|kids"],
            "work": [r"工作|上班|职场|同事|老板|公司", r"work|job|office|boss"],
            "study": [r"学习|考试|作业|知识", r"study|exam|homework|learn"],
            "money": [r"钱|花费|便宜|贵|价格", r"money|cost|price|pay"],
        }

        # Quick mapping to emoji hints
        self.emoji_hints = {
            "joy": "😊",
            "love": "❤️",
            "surprise": "😮",
            "sadness": "😢",
            "anger": "😠",
            "fear": "😨",
            "tired": "😫",
            "thinking": "🤔",
        }

    async def analyze(self, text: str, context: Optional[Dict[str, Any]] = None) -> SemanticAnalysis:
        """Analyze text; try external AI enrichment if configured, else rule-based only."""
        rule_result = self._rule_based(text)

        # Try enrich with external AI if available
        enriched: Optional[Dict[str, Any]] = None
        if self.token and self.modelscope_endpoint and aiohttp is not None:
            try:
                enriched = await self._modelscope_enrich(text, timeout=6.0)
            except Exception as e:
                logger.warning(f"ModelScope enrichment failed: {e}")

        if enriched:
            # Merge: prefer AI emotion if confidence higher, otherwise keep rule
            if enriched.get("confidence", 0) >= max(rule_result.confidence, 0.55):
                emotion = enriched.get("emotion", rule_result.emotion)
                intensity = float(enriched.get("intensity", rule_result.intensity))
                topics = enriched.get("topics") or rule_result.topics
                emoji_hint = enriched.get("emoji") or self.emoji_hints.get(emotion, rule_result.emoji_hint)
                confidence = max(float(enriched.get("confidence", 0.6)), rule_result.confidence)
                reason = f"AI+规则融合: {enriched.get('reason','')}"
                return SemanticAnalysis(emotion, max(0.0, min(intensity, 1.0)), topics, emoji_hint, confidence, reason)

        return rule_result

    def _rule_based(self, text: str) -> SemanticAnalysis:
        t = text.lower()
        # Emotion scoring
        best_emotion = "thinking"
        best_score = 0.0
        matched = []
        for emo, cfg in self.lexicon.items():
            score = 0.0
            for pat in cfg["patterns"]:
                hits = re.findall(pat, t)
                if hits:
                    score += len(hits) * cfg["base"]
                    matched.extend(hits)
            if score > best_score:
                best_score = score
                best_emotion = emo

        # Intensity estimation
        intensity = 0.4 + min(best_score, 2.0) / 2.5  # 0.4 ~ 1.2 before clamp
        if any(re.search(p, t) for p in self.intensifiers):
            intensity += 0.15
        if any(re.search(p, t) for p in self.diminishers):
            intensity -= 0.15
        if any(re.search(p, t) for p in self.negations):
            # Negation reduces intensity and may flip to neutral thinking
            intensity *= 0.6
            if best_score < 0.6:
                best_emotion = "thinking"
        intensity = max(0.0, min(intensity, 1.0))

        # Topics
        topics: List[str] = []
        for name, pats in self.topic_patterns.items():
            for pat in pats:
                if re.search(pat, t):
                    topics.append(name)
                    break

        emoji_hint = self.emoji_hints.get(best_emotion)
        confidence = 0.5 + min(best_score, 1.0) * 0.4
        reason = f"规则匹配: emotion={best_emotion}, hits={matched[:3]}"
        return SemanticAnalysis(best_emotion, float(intensity), topics, emoji_hint, float(confidence), reason)

    async def _modelscope_enrich(self, text: str, timeout: float = 6.0) -> Optional[Dict[str, Any]]:
        if not aiohttp:
            return None
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }
        payload = {
            "text": text,
            # Optional: include a task hint; actual endpoint contract may differ.
            "task": "sentiment_topic_extraction_with_emoji",
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.modelscope_endpoint, headers=headers, json=payload, timeout=timeout) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"HTTP {resp.status}")
                    data = await resp.json(content_type=None)
            except asyncio.TimeoutError:
                raise
            except Exception as e:
                raise RuntimeError(f"request failed: {e}")

        # Expect a normalized schema; if not, try to adapt
        # Target schema: {emotion, intensity:[0,1], topics:[], emoji, confidence:[0,1], reason}
        try:
            if isinstance(data, str):
                data = json.loads(data)
        except Exception:
            pass

        # Best-effort normalization
        emotion = data.get("emotion") or data.get("sentiment") or data.get("label")
        intensity = data.get("intensity") or data.get("score") or 0.6
        topics = data.get("topics") or []
        emoji = data.get("emoji")
        confidence = data.get("confidence") or data.get("probability") or 0.65
        reason = data.get("reason") or data.get("explanation") or "ModelScope分析"

        # Clamp
        try:
            intensity = float(intensity)
        except Exception:
            intensity = 0.6
        intensity = max(0.0, min(float(intensity), 1.0))
        try:
            confidence = float(confidence)
        except Exception:
            confidence = 0.65
        confidence = max(0.0, min(float(confidence), 1.0))

        if not emotion:
            # fallback from topics/keywords
            emotion = "thinking"
        if not emoji:
            emoji = self.emoji_hints.get(emotion, "🤔")

        return {
            "emotion": str(emotion),
            "intensity": intensity,
            "topics": topics if isinstance(topics, list) else [str(topics)],
            "emoji": str(emoji),
            "confidence": confidence,
            "reason": str(reason),
        }
