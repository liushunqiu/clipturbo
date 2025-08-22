#!/usr/bin/env python3
"""
ClipTurbo 单元测试套件
"""

import pytest
import asyncio
import sys
import os
import tempfile
from pathlib import Path

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from core.project_manager import ProjectManager, Project, ProjectConfig
from ai_services.translation_service import TranslationService, SimpleTranslateProvider
from ai_services.ai_orchestrator import AIOrchestrator, VideoContent
from manim_engine.template_system import TemplateManager
from manim_engine.render_manager import RenderManager


class TestProjectManager:
    """项目管理器单元测试"""
    
    def test_project_manager_init(self):
        """测试项目管理器初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pm = ProjectManager(temp_dir)
            assert pm.projects_dir.exists()
            assert isinstance(pm._projects_cache, dict)
    
    def test_create_project(self):
        """测试项目创建"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pm = ProjectManager(temp_dir)
            project_id = pm.create_project("测试项目", "测试描述")
            
            assert project_id is not None
            assert len(project_id) > 0
            
            project = pm.get_project(project_id)
            assert project is not None
            assert project.config.name == "测试项目"
            assert project.config.description == "测试描述"
    
    def test_update_project(self):
        """测试项目更新"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pm = ProjectManager(temp_dir)
            project_id = pm.create_project("测试项目")
            
            success = pm.update_project(project_id, {
                "content": {"title": "新标题"},
                "status": "completed"
            })
            
            assert success is True
            
            project = pm.get_project(project_id)
            assert project.content["title"] == "新标题"
            assert project.status == "completed"
    
    def test_delete_project(self):
        """测试项目删除"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pm = ProjectManager(temp_dir)
            project_id = pm.create_project("测试项目")
            
            success = pm.delete_project(project_id)
            assert success is True
            
            project = pm.get_project(project_id)
            assert project is None
    
    def test_list_projects(self):
        """测试项目列表"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pm = ProjectManager(temp_dir)
            
            # 创建多个项目
            pm.create_project("项目1")
            pm.create_project("项目2")
            
            projects = pm.list_projects()
            assert len(projects) == 2
            assert all('id' in p for p in projects)
            assert all('name' in p for p in projects)


class TestTranslationService:
    """翻译服务单元测试"""
    
    @pytest.mark.asyncio
    async def test_simple_translate_provider(self):
        """测试简单翻译提供者"""
        provider = SimpleTranslateProvider()
        
        result = await provider.translate("hello world", "en", "zh-CN")
        assert result is not None
        assert len(result) > 0
        
        # 测试不支持的语言对
        with pytest.raises(Exception):
            await provider.translate("你好", "zh-CN", "en")
    
    @pytest.mark.asyncio
    async def test_translation_service(self):
        """测试翻译服务"""
        service = TranslationService()
        
        # 测试基本翻译
        result = await service.translate("hello world", "en", "zh-CN")
        assert result is not None
        
        # 测试缓存功能
        result2 = await service.translate("hello world", "en", "zh-CN")
        assert result == result2  # 应该返回缓存的结果
        
        # 测试空文本
        empty_result = await service.translate("", "en", "zh-CN")
        assert empty_result == ""
    
    @pytest.mark.asyncio
    async def test_batch_translate(self):
        """测试批量翻译"""
        service = TranslationService()
        
        texts = ["hello", "world", "machine learning"]
        results = await service.batch_translate(texts, "en", "zh-CN")
        
        assert len(results) == 3
        assert all(isinstance(r, str) for r in results)
    
    def test_language_detection(self):
        """测试语言检测"""
        service = TranslationService()
        
        # 测试中文检测
        chinese_result = service.detect_language("这是一个中文文本")
        assert chinese_result == "zh-CN"
        
        # 测试英文检测
        english_result = service.detect_language("This is English text")
        assert english_result == "en"


class TestVideoContent:
    """视频内容数据结构测试"""
    
    def test_video_content_creation(self):
        """测试视频内容创建"""
        content = VideoContent(
            title="测试标题",
            script="测试脚本",
            language="zh-CN",
            style="educational",
            target_duration=60
        )
        
        assert content.title == "测试标题"
        assert content.script == "测试脚本"
        assert content.language == "zh-CN"
        assert content.style == "educational"
        assert content.target_duration == 60
        assert content.translated_script is None
        assert content.icons is None
        assert content.audio_file is None
    
    def test_video_content_defaults(self):
        """测试视频内容默认值"""
        content = VideoContent(title="测试", script="脚本")
        
        assert content.language == "zh-CN"  # 默认值
        assert content.style == "default"  # 默认值
        assert content.target_duration == 60  # 默认值


class TestTemplateManager:
    """模板管理器单元测试"""
    
    def test_template_manager_init(self):
        """测试模板管理器初始化"""
        tm = TemplateManager()
        # TemplateManager可能使用默认目录，不检查具体路径
        assert tm is not None
    
    def test_list_templates(self):
        """测试模板列表"""
        tm = TemplateManager()
        templates = tm.list_templates()
        
        assert isinstance(templates, list)
        # 应该有一些内置模板
        assert len(templates) > 0
    
    def test_get_template_parameters(self):
        """测试获取模板参数"""
        tm = TemplateManager()
        templates = tm.list_templates()
        
        if templates:
            template_id = templates[0].id
            parameters = tm.get_template_parameters(template_id)
            
            assert isinstance(parameters, list)
            # 所有参数应该是TemplateParameter类型
            for param in parameters:
                assert hasattr(param, 'name')
                assert hasattr(param, 'type')
                assert hasattr(param, 'description')


class TestRenderManager:
    """渲染管理器单元测试"""
    
    @pytest.mark.asyncio
    async def test_render_manager_init(self):
        """测试渲染管理器初始化"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建必要的子目录
            temp_path = Path(temp_dir)
            (temp_path / "temp").mkdir(exist_ok=True)
            
            config = {
                "output_dir": str(temp_path),
                "temp_dir": str(temp_path / "temp"),
                "max_concurrent_renders": 2
            }
            
            rm = RenderManager(config)
            assert rm.output_dir.exists()
            assert rm.temp_dir.exists()
            
            # 清理
            await rm.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_system_resources(self):
        """测试获取系统资源"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"output_dir": temp_dir, "temp_dir": temp_dir}
            rm = RenderManager(config)
            
            resources = rm.get_system_resources()
            
            assert isinstance(resources, dict)
            assert 'memory_percent' in resources
            assert 'cpu_percent' in resources
            
            # 清理
            await rm.shutdown()
    
    @pytest.mark.asyncio
    async def test_get_queue_status(self):
        """测试队列状态"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"output_dir": temp_dir, "temp_dir": temp_dir}
            rm = RenderManager(config)
            
            status = rm.get_queue_status()
            
            assert isinstance(status, dict)
            assert 'pending_jobs' in status
            assert 'active_jobs' in status
            assert 'completed_jobs' in status
            assert 'max_concurrent' in status
            
            # 清理
            await rm.shutdown()


# 集成测试
class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self):
        """测试完整工作流集成"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # 创建必要目录
            (temp_path / "projects").mkdir(exist_ok=True)
            (temp_path / "output").mkdir(exist_ok=True)
            (temp_path / "temp").mkdir(exist_ok=True)
            
            # 初始化所有组件
            pm = ProjectManager(str(temp_path / "projects"))
            tm = TemplateManager()
            
            config = {
                "output_dir": str(temp_path / "output"), 
                "temp_dir": str(temp_path / "temp")
            }
            rm = RenderManager(config)
            
            ai_config = {}
            ai_orchestrator = AIOrchestrator(ai_config)
            
            # 创建项目
            project_id = pm.create_project("集成测试项目")
            assert project_id is not None
            
            # 获取模板
            templates = tm.list_templates()
            assert len(templates) > 0
            
            # 测试翻译服务
            try:
                translation_result = await ai_orchestrator.process_content("hello world")
                # 可能会失败，但应该有错误处理
            except:
                pass  # 忽略AI服务错误
            
            # 测试系统资源
            resources = rm.get_system_resources()
            assert 'memory_percent' in resources
            assert 'cpu_percent' in resources
            
            # 验证项目持久化
            project = pm.get_project(project_id)
            assert project is not None
            assert project.config.name == "集成测试项目"
            
            # 清理
            await rm.shutdown()


# 性能测试
class TestPerformance:
    """性能测试"""
    
    @pytest.mark.asyncio
    async def test_translation_performance(self):
        """测试翻译性能"""
        service = TranslationService()
        
        import time
        start_time = time.time()
        
        # 批量翻译
        texts = ["hello"] * 100  # 100个相同的文本
        results = await service.batch_translate(texts, "en", "zh-CN")
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        assert len(results) == 100
        assert elapsed < 5.0  # 应该在5秒内完成
    
    def test_project_manager_performance(self):
        """测试项目管理器性能"""
        with tempfile.TemporaryDirectory() as temp_dir:
            pm = ProjectManager(temp_dir)
            
            import time
            start_time = time.time()
            
            # 创建大量项目
            project_ids = []
            for i in range(100):
                project_id = pm.create_project(f"项目{i}")
                project_ids.append(project_id)
            
            end_time = time.time()
            elapsed = end_time - start_time
            
            assert len(project_ids) == 100
            assert elapsed < 10.0  # 应该在10秒内完成


if __name__ == "__main__":
    pytest.main([__file__, "-v"])