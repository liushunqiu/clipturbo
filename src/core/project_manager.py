"""
Project Manager - 项目管理器
"""

import json
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from pathlib import Path
from datetime import datetime
import logging


@dataclass
class ProjectConfig:
    """项目配置"""
    name: str
    description: str = ""
    template_id: str = "simple_text"
    video_settings: Dict[str, Any] = field(default_factory=dict)
    ai_settings: Dict[str, Any] = field(default_factory=dict)
    render_settings: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Project:
    """项目数据结构"""
    id: str
    config: ProjectConfig
    content: Dict[str, Any] = field(default_factory=dict)
    assets: Dict[str, str] = field(default_factory=dict)  # 资源文件路径
    history: List[Dict[str, Any]] = field(default_factory=list)  # 操作历史
    status: str = "draft"  # draft, processing, completed, failed


class ProjectManager:
    """项目管理器"""
    
    def __init__(self, projects_dir: str = "./projects"):
        self.projects_dir = Path(projects_dir)
        self.projects_dir.mkdir(exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # 项目缓存
        self._projects_cache: Dict[str, Project] = {}
        
        # 加载现有项目
        self._load_projects()
    
    def _load_projects(self):
        """加载现有项目"""
        try:
            for project_file in self.projects_dir.glob("*.json"):
                try:
                    with open(project_file, 'r', encoding='utf-8') as f:
                        project_data = json.load(f)
                    
                    # 手动构建Project对象，确保dataclass正确创建
                    config_data = project_data.get('config', {})
                    project_config = ProjectConfig(**config_data)
                    
                    project = Project(
                        id=project_data['id'],
                        config=project_config,
                        content=project_data.get('content', {}),
                        assets=project_data.get('assets', {}),
                        history=project_data.get('history', []),
                        status=project_data.get('status', 'draft')
                    )
                    self._projects_cache[project.id] = project
                    
                except Exception as e:
                    self.logger.warning(f"加载项目文件失败 {project_file}: {str(e)}")
            
            self.logger.info(f"加载了 {len(self._projects_cache)} 个项目")
            
        except Exception as e:
            self.logger.error(f"加载项目失败: {str(e)}")
    
    def create_project(
        self,
        name: str,
        description: str = "",
        template_id: str = "simple_text",
        project_id: Optional[str] = None
    ) -> str:
        """创建新项目"""
        if project_id is None:
            project_id = str(uuid.uuid4())
        
        # 创建项目配置
        config = ProjectConfig(
            name=name,
            description=description,
            template_id=template_id,
            video_settings={
                'resolution': [1920, 1080],
                'frame_rate': 30,
                'duration': 60,
                'aspect_ratio': '16:9'
            },
            ai_settings={
                'language': 'zh-CN',
                'style': 'default',
                'voice': 'default'
            },
            render_settings={
                'quality': 'medium_quality',
                'background_color': 'BLACK'
            }
        )
        
        # 创建项目
        project = Project(
            id=project_id,
            config=config
        )
        
        # 添加创建历史记录
        project.history.append({
            'action': 'created',
            'timestamp': datetime.now().isoformat(),
            'details': {'name': name, 'template_id': template_id}
        })
        
        # 保存项目
        self._save_project(project)
        self._projects_cache[project_id] = project
        
        self.logger.info(f"创建项目: {name} ({project_id})")
        return project_id
    
    def get_project(self, project_id: str) -> Optional[Project]:
        """获取项目"""
        return self._projects_cache.get(project_id)
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> bool:
        """更新项目"""
        project = self.get_project(project_id)
        if not project:
            return False
        
        try:
            # 更新配置
            if 'config' in updates:
                for key, value in updates['config'].items():
                    if hasattr(project.config, key):
                        setattr(project.config, key, value)
            
            # 更新内容
            if 'content' in updates:
                project.content.update(updates['content'])
            
            # 更新资源
            if 'assets' in updates:
                project.assets.update(updates['assets'])
            
            # 更新状态
            if 'status' in updates:
                project.status = updates['status']
            
            # 更新时间戳
            project.config.updated_at = datetime.now().isoformat()
            
            # 添加历史记录
            project.history.append({
                'action': 'updated',
                'timestamp': datetime.now().isoformat(),
                'details': updates
            })
            
            # 保存项目
            self._save_project(project)
            
            self.logger.info(f"更新项目: {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新项目失败 {project_id}: {str(e)}")
            return False
    
    def delete_project(self, project_id: str) -> bool:
        """删除项目"""
        if project_id not in self._projects_cache:
            return False
        
        try:
            # 删除项目文件
            project_file = self.projects_dir / f"{project_id}.json"
            if project_file.exists():
                project_file.unlink()
            
            # 删除项目资源目录
            project_assets_dir = self.projects_dir / project_id
            if project_assets_dir.exists():
                import shutil
                shutil.rmtree(project_assets_dir)
            
            # 从缓存中移除
            del self._projects_cache[project_id]
            
            self.logger.info(f"删除项目: {project_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"删除项目失败 {project_id}: {str(e)}")
            return False
    
    def list_projects(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """列出项目"""
        projects = []
        
        for project in self._projects_cache.values():
            if status is None or project.status == status:
                projects.append({
                    'id': project.id,
                    'name': project.config.name,
                    'description': project.config.description,
                    'template_id': project.config.template_id,
                    'status': project.status,
                    'created_at': project.config.created_at,
                    'updated_at': project.config.updated_at
                })
        
        # 按更新时间排序
        projects.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return projects
    
    def duplicate_project(self, project_id: str, new_name: Optional[str] = None) -> Optional[str]:
        """复制项目"""
        source_project = self.get_project(project_id)
        if not source_project:
            return None
        
        try:
            # 生成新的项目ID
            new_project_id = str(uuid.uuid4())
            
            # 复制项目配置
            new_config = ProjectConfig(**asdict(source_project.config))
            new_config.name = new_name or f"{source_project.config.name} (副本)"
            new_config.created_at = datetime.now().isoformat()
            new_config.updated_at = datetime.now().isoformat()
            
            # 创建新项目
            new_project = Project(
                id=new_project_id,
                config=new_config,
                content=source_project.content.copy(),
                assets=source_project.assets.copy(),
                status="draft"
            )
            
            # 添加历史记录
            new_project.history.append({
                'action': 'duplicated',
                'timestamp': datetime.now().isoformat(),
                'details': {'source_project_id': project_id}
            })
            
            # 保存新项目
            self._save_project(new_project)
            self._projects_cache[new_project_id] = new_project
            
            self.logger.info(f"复制项目: {project_id} -> {new_project_id}")
            return new_project_id
            
        except Exception as e:
            self.logger.error(f"复制项目失败 {project_id}: {str(e)}")
            return None
    
    def export_project(self, project_id: str, export_path: str) -> bool:
        """导出项目"""
        project = self.get_project(project_id)
        if not project:
            return False
        
        try:
            export_data = {
                'project': asdict(project),
                'export_time': datetime.now().isoformat(),
                'version': '1.0'
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"导出项目: {project_id} -> {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"导出项目失败 {project_id}: {str(e)}")
            return False
    
    def import_project(self, import_path: str) -> Optional[str]:
        """导入项目"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            project_data = import_data['project']
            
            # 生成新的项目ID
            new_project_id = str(uuid.uuid4())
            project_data['id'] = new_project_id
            
            # 创建项目对象
            project = Project(**project_data)
            
            # 更新时间戳
            project.config.created_at = datetime.now().isoformat()
            project.config.updated_at = datetime.now().isoformat()
            
            # 添加导入历史记录
            project.history.append({
                'action': 'imported',
                'timestamp': datetime.now().isoformat(),
                'details': {'import_path': import_path}
            })
            
            # 保存项目
            self._save_project(project)
            self._projects_cache[new_project_id] = project
            
            self.logger.info(f"导入项目: {import_path} -> {new_project_id}")
            return new_project_id
            
        except Exception as e:
            self.logger.error(f"导入项目失败 {import_path}: {str(e)}")
            return None
    
    def get_project_assets_dir(self, project_id: str) -> Path:
        """获取项目资源目录"""
        assets_dir = self.projects_dir / project_id
        assets_dir.mkdir(exist_ok=True)
        return assets_dir
    
    def add_project_asset(self, project_id: str, asset_name: str, asset_path: str) -> bool:
        """添加项目资源"""
        project = self.get_project(project_id)
        if not project:
            return False
        
        try:
            # 复制资源文件到项目目录
            assets_dir = self.get_project_assets_dir(project_id)
            target_path = assets_dir / asset_name
            
            import shutil
            shutil.copy2(asset_path, target_path)
            
            # 更新项目资源记录
            project.assets[asset_name] = str(target_path)
            
            # 保存项目
            self._save_project(project)
            
            self.logger.info(f"添加项目资源: {project_id} - {asset_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"添加项目资源失败 {project_id}: {str(e)}")
            return False
    
    def _save_project(self, project: Project):
        """保存项目到文件"""
        try:
            project_file = self.projects_dir / f"{project.id}.json"
            
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(project), f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存项目失败 {project.id}: {str(e)}")
            raise
    
    def search_projects(self, query: str) -> List[Dict[str, Any]]:
        """搜索项目"""
        query_lower = query.lower()
        matching_projects = []
        
        for project in self._projects_cache.values():
            if (query_lower in project.config.name.lower() or
                query_lower in project.config.description.lower() or
                query_lower in project.config.template_id.lower()):
                
                matching_projects.append({
                    'id': project.id,
                    'name': project.config.name,
                    'description': project.config.description,
                    'template_id': project.config.template_id,
                    'status': project.status,
                    'created_at': project.config.created_at,
                    'updated_at': project.config.updated_at
                })
        
        # 按相关性和更新时间排序
        matching_projects.sort(key=lambda x: x['updated_at'], reverse=True)
        
        return matching_projects
    
    def get_project_statistics(self) -> Dict[str, Any]:
        """获取项目统计信息"""
        total_projects = len(self._projects_cache)
        
        status_counts = {}
        template_counts = {}
        
        for project in self._projects_cache.values():
            # 统计状态
            status = project.status
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # 统计模板使用
            template_id = project.config.template_id
            template_counts[template_id] = template_counts.get(template_id, 0) + 1
        
        return {
            'total_projects': total_projects,
            'status_distribution': status_counts,
            'template_usage': template_counts,
            'projects_dir': str(self.projects_dir)
        }
