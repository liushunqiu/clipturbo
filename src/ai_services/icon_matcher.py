"""
Icon Matcher - 图标和图片匹配服务
"""

import asyncio
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging
import aiohttp
import json
import re
from pathlib import Path


@dataclass
class IconResult:
    """图标搜索结果"""
    url: str
    title: str
    description: str
    tags: List[str]
    source: str  # 来源: unsplash, pexels, local, etc.
    license: str
    size: Optional[Tuple[int, int]] = None
    file_size: Optional[int] = None


class IconProvider(ABC):
    """图标提供者抽象基类"""
    
    @abstractmethod
    async def search_icons(
        self, 
        keywords: List[str], 
        count: int = 10,
        style: str = 'default'
    ) -> List[IconResult]:
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        pass


class UnsplashProvider(IconProvider):
    """Unsplash图片提供者"""
    
    def __init__(self, access_key: str):
        self.access_key = access_key
        self.base_url = "https://api.unsplash.com"
        self.logger = logging.getLogger(__name__)
    
    async def search_icons(
        self, 
        keywords: List[str], 
        count: int = 10,
        style: str = 'default'
    ) -> List[IconResult]:
        try:
            query = ' '.join(keywords)
            
            headers = {
                'Authorization': f'Client-ID {self.access_key}'
            }
            
            params = {
                'query': query,
                'per_page': min(count, 30),
                'orientation': 'landscape' if style == 'landscape' else 'squarish'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search/photos",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_unsplash_results(data['results'])
                    else:
                        raise Exception(f"Unsplash API错误: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Unsplash搜索失败: {str(e)}")
            return []
    
    def _parse_unsplash_results(self, results: List[Dict]) -> List[IconResult]:
        """解析Unsplash搜索结果"""
        icons = []
        
        for item in results:
            icon = IconResult(
                url=item['urls']['regular'],
                title=item.get('description') or item.get('alt_description', ''),
                description=item.get('description', ''),
                tags=item.get('tags', []),
                source='unsplash',
                license='Unsplash License',
                size=(item['width'], item['height'])
            )
            icons.append(icon)
        
        return icons
    
    def is_available(self) -> bool:
        return bool(self.access_key)


class PexelsProvider(IconProvider):
    """Pexels图片提供者"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pexels.com/v1"
        self.logger = logging.getLogger(__name__)
    
    async def search_icons(
        self, 
        keywords: List[str], 
        count: int = 10,
        style: str = 'default'
    ) -> List[IconResult]:
        try:
            query = ' '.join(keywords)
            
            headers = {
                'Authorization': self.api_key
            }
            
            params = {
                'query': query,
                'per_page': min(count, 80),
                'orientation': 'landscape' if style == 'landscape' else 'square'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/search",
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_pexels_results(data['photos'])
                    else:
                        raise Exception(f"Pexels API错误: {response.status}")
                        
        except Exception as e:
            self.logger.error(f"Pexels搜索失败: {str(e)}")
            return []
    
    def _parse_pexels_results(self, results: List[Dict]) -> List[IconResult]:
        """解析Pexels搜索结果"""
        icons = []
        
        for item in results:
            icon = IconResult(
                url=item['src']['medium'],
                title=item.get('alt', ''),
                description=item.get('alt', ''),
                tags=[],
                source='pexels',
                license='Pexels License',
                size=(item['width'], item['height'])
            )
            icons.append(icon)
        
        return icons
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class LocalIconProvider(IconProvider):
    """本地图标库提供者"""
    
    def __init__(self, icon_directory: str):
        self.icon_directory = Path(icon_directory)
        self.logger = logging.getLogger(__name__)
        
        # 加载本地图标索引
        self.icon_index = self._build_icon_index()
    
    def _build_icon_index(self) -> Dict[str, List[str]]:
        """构建本地图标索引"""
        index = {}
        
        if not self.icon_directory.exists():
            return index
        
        # 扫描图标文件
        for icon_file in self.icon_directory.rglob('*'):
            if icon_file.suffix.lower() in ['.png', '.jpg', '.jpeg', '.svg', '.webp']:
                # 从文件名提取关键词
                keywords = self._extract_keywords_from_filename(icon_file.name)
                
                for keyword in keywords:
                    if keyword not in index:
                        index[keyword] = []
                    index[keyword].append(str(icon_file))
        
        return index
    
    def _extract_keywords_from_filename(self, filename: str) -> List[str]:
        """从文件名提取关键词"""
        # 移除扩展名
        name = Path(filename).stem
        
        # 分割关键词（支持下划线、连字符、驼峰命名）
        keywords = re.split(r'[_\-\s]+|(?<=[a-z])(?=[A-Z])', name.lower())
        
        # 过滤空字符串和单字符
        keywords = [kw for kw in keywords if len(kw) > 1]
        
        return keywords
    
    async def search_icons(
        self, 
        keywords: List[str], 
        count: int = 10,
        style: str = 'default'
    ) -> List[IconResult]:
        """搜索本地图标"""
        matched_files = set()
        
        # 搜索匹配的文件
        for keyword in keywords:
            keyword = keyword.lower()
            for indexed_keyword, files in self.icon_index.items():
                if keyword in indexed_keyword or indexed_keyword in keyword:
                    matched_files.update(files)
        
        # 转换为IconResult
        results = []
        for file_path in list(matched_files)[:count]:
            path = Path(file_path)
            if path.exists():
                icon = IconResult(
                    url=f"file://{file_path}",
                    title=path.stem,
                    description=f"本地图标: {path.name}",
                    tags=self._extract_keywords_from_filename(path.name),
                    source='local',
                    license='Local',
                    file_size=path.stat().st_size
                )
                results.append(icon)
        
        return results
    
    def is_available(self) -> bool:
        return self.icon_directory.exists() and len(self.icon_index) > 0


class IconMatcher:
    """图标匹配服务"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 初始化图标提供者
        self.providers = []
        self._init_providers()
        
        # 关键词提取配置
        self.keyword_patterns = {
            'zh': r'[\u4e00-\u9fff]+',  # 中文
            'en': r'[a-zA-Z]+',        # 英文
        }
        
        # 缓存
        self._cache = {}
        self.cache_enabled = config.get('cache_enabled', True)
    
    def _init_providers(self):
        """初始化图标提供者"""
        # Unsplash提供者
        if self.config.get('unsplash', {}).get('access_key'):
            try:
                provider = UnsplashProvider(
                    access_key=self.config['unsplash']['access_key']
                )
                self.providers.append(provider)
                self.logger.info("Unsplash提供者初始化成功")
            except Exception as e:
                self.logger.warning(f"Unsplash提供者初始化失败: {str(e)}")
        
        # Pexels提供者
        if self.config.get('pexels', {}).get('api_key'):
            try:
                provider = PexelsProvider(
                    api_key=self.config['pexels']['api_key']
                )
                self.providers.append(provider)
                self.logger.info("Pexels提供者初始化成功")
            except Exception as e:
                self.logger.warning(f"Pexels提供者初始化失败: {str(e)}")
        
        # 本地图标提供者
        if self.config.get('local', {}).get('icon_directory'):
            try:
                provider = LocalIconProvider(
                    icon_directory=self.config['local']['icon_directory']
                )
                self.providers.append(provider)
                self.logger.info("本地图标提供者初始化成功")
            except Exception as e:
                self.logger.warning(f"本地图标提供者初始化失败: {str(e)}")
    
    async def find_matching_icons(
        self,
        text: str,
        style: str = 'default',
        count: int = 5,
        provider_preference: Optional[str] = None
    ) -> List[IconResult]:
        """
        根据文本内容查找匹配的图标
        
        Args:
            text: 文本内容
            style: 图标风格
            count: 返回数量
            provider_preference: 优先使用的提供者
            
        Returns:
            匹配的图标列表
        """
        # 提取关键词
        keywords = self._extract_keywords(text)
        if not keywords:
            return []
        
        # 检查缓存
        cache_key = f"{hash(text)}_{style}_{count}"
        if self.cache_enabled and cache_key in self._cache:
            return self._cache[cache_key]
        
        # 搜索图标
        all_results = []
        
        # 按优先级排序提供者
        sorted_providers = self._sort_providers_by_preference(provider_preference)
        
        for provider in sorted_providers:
            if provider.is_available():
                try:
                    results = await provider.search_icons(keywords, count, style)
                    all_results.extend(results)
                    
                    # 如果已经有足够的结果，可以提前结束
                    if len(all_results) >= count:
                        break
                        
                except Exception as e:
                    self.logger.warning(f"提供者 {provider.__class__.__name__} 搜索失败: {str(e)}")
                    continue
        
        # 去重和排序
        unique_results = self._deduplicate_and_rank(all_results, keywords)
        final_results = unique_results[:count]
        
        # 缓存结果
        if self.cache_enabled:
            self._cache[cache_key] = final_results
        
        return final_results
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        keywords = []
        
        # 中文关键词提取
        chinese_words = re.findall(self.keyword_patterns['zh'], text)
        keywords.extend([word for word in chinese_words if len(word) >= 2])
        
        # 英文关键词提取
        english_words = re.findall(self.keyword_patterns['en'], text.lower())
        keywords.extend([word for word in english_words if len(word) >= 3])
        
        # 移除停用词
        stop_words = {'的', '是', '在', '有', '和', '与', '或', '但', '因为', 'the', 'is', 'in', 'and', 'or', 'but', 'because'}
        keywords = [kw for kw in keywords if kw not in stop_words]
        
        # 去重并保持顺序
        seen = set()
        unique_keywords = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique_keywords.append(kw)
        
        return unique_keywords[:10]  # 限制关键词数量
    
    def _sort_providers_by_preference(self, preference: Optional[str]) -> List[IconProvider]:
        """根据偏好排序提供者"""
        if not preference:
            return self.providers
        
        # 将偏好的提供者放在前面
        preferred_providers = []
        other_providers = []
        
        for provider in self.providers:
            if preference.lower() in provider.__class__.__name__.lower():
                preferred_providers.append(provider)
            else:
                other_providers.append(provider)
        
        return preferred_providers + other_providers
    
    def _deduplicate_and_rank(
        self, 
        results: List[IconResult], 
        keywords: List[str]
    ) -> List[IconResult]:
        """去重并按相关性排序"""
        # 简单去重（基于URL）
        seen_urls = set()
        unique_results = []
        
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)
        
        # 按相关性评分排序
        def calculate_relevance_score(icon: IconResult) -> float:
            score = 0.0
            
            # 标题匹配
            title_lower = icon.title.lower()
            for keyword in keywords:
                if keyword.lower() in title_lower:
                    score += 2.0
            
            # 标签匹配
            for tag in icon.tags:
                tag_lower = tag.lower() if isinstance(tag, str) else str(tag).lower()
                for keyword in keywords:
                    if keyword.lower() in tag_lower:
                        score += 1.0
            
            # 描述匹配
            desc_lower = icon.description.lower()
            for keyword in keywords:
                if keyword.lower() in desc_lower:
                    score += 0.5
            
            # 来源权重
            source_weights = {
                'local': 1.2,    # 本地图标优先
                'unsplash': 1.0,
                'pexels': 0.9
            }
            score *= source_weights.get(icon.source, 1.0)
            
            return score
        
        # 排序
        unique_results.sort(key=calculate_relevance_score, reverse=True)
        
        return unique_results
    
    async def batch_find_icons(
        self,
        texts: List[str],
        style: str = 'default',
        count: int = 5
    ) -> List[List[IconResult]]:
        """批量查找图标"""
        tasks = [
            self.find_matching_icons(text, style, count)
            for text in texts
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        icon_lists = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.error(f"查找文本 '{texts[i][:50]}...' 的图标失败: {str(result)}")
                icon_lists.append([])
            else:
                icon_lists.append(result)
        
        return icon_lists
    
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
        """清空图标缓存"""
        self._cache.clear()
        self.logger.info("图标缓存已清空")
    
    def add_local_icons(self, icon_directory: str):
        """添加本地图标目录"""
        try:
            provider = LocalIconProvider(icon_directory)
            if provider.is_available():
                self.providers.append(provider)
                self.logger.info(f"添加本地图标目录成功: {icon_directory}")
                return True
        except Exception as e:
            self.logger.error(f"添加本地图标目录失败: {str(e)}")
        
        return False
