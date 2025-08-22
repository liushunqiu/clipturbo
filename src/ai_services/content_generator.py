"""
Content Generator - AI文案生成服务
"""

import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import openai
import logging
from abc import ABC, abstractmethod


@dataclass
class ContentStyle:
    """内容风格定义"""
    name: str
    description: str
    tone: str  # 语调: formal, casual, humorous, professional
    structure: str  # 结构: narrative, list, qa, tutorial
    keywords: List[str]  # 关键词


class ContentProvider(ABC):
    """内容生成提供者抽象基类"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass


class OpenAIProvider(ContentProvider):
    """OpenAI GPT 内容生成器"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是一个专业的短视频文案创作专家，擅长创作吸引人的短视频内容。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=kwargs.get('max_tokens', 1000),
                temperature=kwargs.get('temperature', 0.7)
            )
            return response.choices[0].message.content
        except Exception as e:
            self.logger.error(f"OpenAI生成失败: {str(e)}")
            raise
    
    def is_available(self) -> bool:
        return hasattr(self, 'client') and self.client is not None


class LocalModelProvider(ContentProvider):
    """本地模型内容生成器"""
    
    def __init__(self, model_path: str):
        self.model_path = model_path
        self.model = None
        self.logger = logging.getLogger(__name__)
        # TODO: 集成本地模型 (如 Ollama, Transformers)
    
    async def generate(self, prompt: str, **kwargs) -> str:
        # 占位实现，实际需要集成具体的本地模型
        return f"本地模型生成的内容: {prompt[:50]}..."
    
    def is_available(self) -> bool:
        return self.model is not None


class ContentGenerator:
    """AI内容生成服务"""
    
    # 预定义内容风格
    STYLES = {
        'default': ContentStyle(
            name='默认',
            description='通用短视频风格',
            tone='casual',
            structure='narrative',
            keywords=['有趣', '实用', '分享']
        ),
        'educational': ContentStyle(
            name='教育科普',
            description='知识分享类视频',
            tone='professional',
            structure='tutorial',
            keywords=['学习', '知识', '技巧', '方法']
        ),
        'entertainment': ContentStyle(
            name='娱乐搞笑',
            description='轻松娱乐类视频',
            tone='humorous',
            structure='narrative',
            keywords=['搞笑', '有趣', '娱乐', '轻松']
        ),
        'lifestyle': ContentStyle(
            name='生活方式',
            description='生活分享类视频',
            tone='casual',
            structure='list',
            keywords=['生活', '分享', '体验', '推荐']
        ),
        'business': ContentStyle(
            name='商业营销',
            description='商业推广类视频',
            tone='professional',
            structure='qa',
            keywords=['产品', '服务', '优势', '价值']
        )
    }
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化内容提供者
        self.providers = []
        self._init_providers()
        
        # 当前使用的提供者
        self.current_provider = self.providers[0] if self.providers else None
    
    def _init_providers(self):
        """初始化内容生成提供者"""
        # OpenAI 提供者
        if self.config.get('openai', {}).get('api_key'):
            try:
                provider = OpenAIProvider(
                    api_key=self.config['openai']['api_key'],
                    model=self.config['openai'].get('model', 'gpt-3.5-turbo')
                )
                self.providers.append(provider)
                self.logger.info("OpenAI提供者初始化成功")
            except Exception as e:
                self.logger.warning(f"OpenAI提供者初始化失败: {str(e)}")
        
        # 本地模型提供者
        if self.config.get('local_model', {}).get('model_path'):
            try:
                provider = LocalModelProvider(
                    model_path=self.config['local_model']['model_path']
                )
                self.providers.append(provider)
                self.logger.info("本地模型提供者初始化成功")
            except Exception as e:
                self.logger.warning(f"本地模型提供者初始化失败: {str(e)}")
    
    async def generate_video_script(
        self,
        topic: str,
        style: str = 'default',
        duration: int = 60,
        language: str = 'zh-CN'
    ) -> Dict[str, Any]:
        """
        生成视频脚本
        
        Args:
            topic: 视频主题
            style: 内容风格
            duration: 目标时长(秒)
            language: 语言
            
        Returns:
            Dict包含: title, script, hooks, tags, description
        """
        if not self.current_provider:
            raise Exception("没有可用的内容生成提供者")
        
        # 获取风格配置
        style_config = self.STYLES.get(style, self.STYLES['default'])
        
        # 构建提示词
        prompt = self._build_script_prompt(topic, style_config, duration, language)
        
        try:
            # 生成内容
            content = await self.current_provider.generate(
                prompt=prompt,
                max_tokens=1500,
                temperature=0.7
            )
            
            # 解析生成的内容
            parsed_content = self._parse_generated_content(content)
            
            return {
                'title': parsed_content.get('title', topic),
                'script': parsed_content.get('script', content),
                'hooks': parsed_content.get('hooks', []),
                'tags': parsed_content.get('tags', []),
                'description': parsed_content.get('description', ''),
                'style': style,
                'estimated_duration': self._estimate_duration(parsed_content.get('script', content))
            }
            
        except Exception as e:
            self.logger.error(f"脚本生成失败: {str(e)}")
            # 尝试使用备用提供者
            if len(self.providers) > 1:
                return await self._fallback_generate(topic, style, duration, language)
            raise
    
    def _build_script_prompt(
        self,
        topic: str,
        style: ContentStyle,
        duration: int,
        language: str
    ) -> str:
        """构建脚本生成提示词"""
        
        word_count = duration * 3  # 估算每秒3个字
        
        prompt = f"""
请为以下主题创作一个{duration}秒的短视频脚本：

主题：{topic}
风格：{style.description}
语调：{style.tone}
结构：{style.structure}
目标字数：约{word_count}字
语言：{language}

要求：
1. 开头要有吸引人的钩子，能在3秒内抓住观众注意力
2. 内容要简洁有力，适合短视频传播
3. 结尾要有明确的行动号召或总结
4. 语言要符合{style.tone}的语调
5. 融入关键词：{', '.join(style.keywords)}

请按以下格式输出：

标题：[视频标题]

脚本：
[完整的视频脚本内容]

钩子：
[开头吸引人的句子]

标签：
[相关的话题标签，用逗号分隔]

描述：
[视频描述文案]
"""
        return prompt
    
    def _parse_generated_content(self, content: str) -> Dict[str, Any]:
        """解析生成的内容"""
        result = {}
        
        lines = content.strip().split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if line.startswith('标题：'):
                if current_section:
                    result[current_section] = '\n'.join(current_content)
                current_section = 'title'
                current_content = [line.replace('标题：', '').strip()]
            elif line.startswith('脚本：'):
                if current_section:
                    result[current_section] = '\n'.join(current_content)
                current_section = 'script'
                current_content = []
            elif line.startswith('钩子：'):
                if current_section:
                    result[current_section] = '\n'.join(current_content)
                current_section = 'hooks'
                current_content = [line.replace('钩子：', '').strip()]
            elif line.startswith('标签：'):
                if current_section:
                    result[current_section] = '\n'.join(current_content)
                current_section = 'tags'
                tags = line.replace('标签：', '').strip()
                current_content = [tag.strip() for tag in tags.split(',')]
            elif line.startswith('描述：'):
                if current_section:
                    result[current_section] = '\n'.join(current_content)
                current_section = 'description'
                current_content = [line.replace('描述：', '').strip()]
            else:
                current_content.append(line)
        
        # 处理最后一个section
        if current_section:
            if current_section == 'tags':
                result[current_section] = current_content
            else:
                result[current_section] = '\n'.join(current_content)
        
        return result
    
    def _estimate_duration(self, script: str) -> int:
        """估算脚本时长"""
        # 简单估算：中文每秒约3个字，英文每秒约2个词
        char_count = len(script.replace(' ', '').replace('\n', ''))
        return max(10, char_count // 3)  # 最少10秒
    
    async def _fallback_generate(
        self,
        topic: str,
        style: str,
        duration: int,
        language: str
    ) -> Dict[str, Any]:
        """备用生成方法"""
        for provider in self.providers[1:]:
            if provider.is_available():
                try:
                    self.current_provider = provider
                    return await self.generate_video_script(topic, style, duration, language)
                except Exception as e:
                    self.logger.warning(f"备用提供者失败: {str(e)}")
                    continue
        
        raise Exception("所有内容生成提供者都不可用")
    
    async def generate_batch_scripts(
        self,
        topics: List[str],
        style: str = 'default',
        duration: int = 60,
        language: str = 'zh-CN'
    ) -> List[Dict[str, Any]]:
        """批量生成脚本"""
        tasks = [
            self.generate_video_script(topic, style, duration, language)
            for topic in topics
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 过滤异常结果
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"生成主题 '{topics[i]}' 失败: {str(result)}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def get_available_styles(self) -> Dict[str, ContentStyle]:
        """获取可用的内容风格"""
        return self.STYLES.copy()
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.current_provider is not None and self.current_provider.is_available()
    
    def switch_provider(self, provider_index: int) -> bool:
        """切换内容提供者"""
        if 0 <= provider_index < len(self.providers):
            if self.providers[provider_index].is_available():
                self.current_provider = self.providers[provider_index]
                return True
        return False
