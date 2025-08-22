"""
Workflow Engine - 视频生成工作流引擎
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import time
import json

from ..ai_services import AIOrchestrator, VideoContent
from ..manim_engine import TemplateManager, RenderManager, RenderConfig, RenderQuality


class StepStatus(Enum):
    """工作流步骤状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    """工作流状态"""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """工作流步骤"""
    id: str
    name: str
    description: str
    handler: Callable
    dependencies: List[str] = field(default_factory=list)
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    progress: float = 0.0


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    workflow_id: str
    status: WorkflowStatus
    steps: Dict[str, WorkflowStep]
    start_time: float
    end_time: Optional[float]
    total_duration: float
    output_files: List[str] = field(default_factory=list)
    error_message: Optional[str] = None


class WorkflowEngine:
    """工作流引擎 - 协调整个视频生成流程"""
    
    def __init__(
        self,
        ai_orchestrator: AIOrchestrator,
        template_manager: TemplateManager,
        render_manager: RenderManager
    ):
        self.ai_orchestrator = ai_orchestrator
        self.template_manager = template_manager
        self.render_manager = render_manager
        self.logger = logging.getLogger(__name__)
        
        # 活跃的工作流
        self.active_workflows: Dict[str, WorkflowResult] = {}
        
        # 预定义工作流步骤
        self.step_handlers = {
            'content_generation': self._handle_content_generation,
            'content_preparation': self._handle_content_preparation,
            'template_selection': self._handle_template_selection,
            'parameter_preparation': self._handle_parameter_preparation,
            'scene_creation': self._handle_scene_creation,
            'video_rendering': self._handle_video_rendering,
            'post_processing': self._handle_post_processing
        }
    
    async def create_video_workflow(
        self,
        content_input: Union[str, Dict[str, Any]],
        requirements: Dict[str, Any],
        workflow_id: Optional[str] = None
    ) -> str:
        """
        创建完整的视频生成工作流
        
        Args:
            content_input: 内容输入，可以是主题(str)或完整的视频内容(dict)
            requirements: 生成要求
            workflow_id: 工作流ID（可选）
            
        Returns:
            工作流ID
        """
        if workflow_id is None:
            workflow_id = f"workflow_{int(time.time() * 1000)}"
        
        # 判断是否需要AI生成内容
        use_ai_generation = isinstance(content_input, str)
        
        # 定义工作流步骤
        steps = {}
        
        if use_ai_generation:
            # 使用AI生成内容的完整流程
            steps = {
                'content_generation': WorkflowStep(
                    id='content_generation',
                    name='内容生成',
                    description='使用AI生成视频内容',
                    handler=self.step_handlers['content_generation']
                ),
                'template_selection': WorkflowStep(
                    id='template_selection',
                    name='模板选择',
                    description='选择合适的视频模板',
                    handler=self.step_handlers['template_selection'],
                    dependencies=['content_generation']
                ),
                'parameter_preparation': WorkflowStep(
                    id='parameter_preparation',
                    name='参数准备',
                    description='准备模板参数',
                    handler=self.step_handlers['parameter_preparation'],
                    dependencies=['content_generation', 'template_selection']
                ),
            }
        else:
            # 直接使用提供的内容
            steps = {
                'content_preparation': WorkflowStep(
                    id='content_preparation',
                    name='内容准备',
                    description='处理用户提供的视频内容',
                    handler=self.step_handlers['content_preparation']
                ),
                'template_selection': WorkflowStep(
                    id='template_selection',
                    name='模板选择',
                    description='选择合适的视频模板',
                    handler=self.step_handlers['template_selection'],
                    dependencies=['content_preparation']
                ),
                'parameter_preparation': WorkflowStep(
                    id='parameter_preparation',
                    name='参数准备',
                    description='准备模板参数',
                    handler=self.step_handlers['parameter_preparation'],
                    dependencies=['content_preparation', 'template_selection']
                ),
            }
        
        # 共同的后续步骤
        steps.update({
            'scene_creation': WorkflowStep(
                id='scene_creation',
                name='场景创建',
                description='创建Manim场景',
                handler=self.step_handlers['scene_creation'],
                dependencies=['parameter_preparation']
            ),
            'video_rendering': WorkflowStep(
                id='video_rendering',
                name='视频渲染',
                description='渲染最终视频',
                handler=self.step_handlers['video_rendering'],
                dependencies=['scene_creation']
            ),
            'post_processing': WorkflowStep(
                id='post_processing',
                name='后期处理',
                description='视频后期处理',
                handler=self.step_handlers['post_processing'],
                dependencies=['video_rendering']
            )
        })
        
        # 创建工作流结果对象
        workflow_result = WorkflowResult(
            workflow_id=workflow_id,
            status=WorkflowStatus.CREATED,
            steps=steps,
            start_time=time.time(),
            end_time=None,
            total_duration=0.0
        )
        
        # 存储工作流上下文
        workflow_result.context = {
            'content_input': content_input,
            'requirements': requirements,
            'video_content': None,
            'selected_template': None,
            'template_parameters': None,
            'scene_class': None,
            'render_job_id': None,
            'use_ai_generation': use_ai_generation
        }
        
        self.active_workflows[workflow_id] = workflow_result
        
        # 启动工作流执行
        asyncio.create_task(self._execute_workflow(workflow_id))
        
        self.logger.info(f"创建视频生成工作流: {workflow_id}")
        return workflow_id
    
    async def _execute_workflow(self, workflow_id: str):
        """执行工作流"""
        try:
            workflow = self.active_workflows[workflow_id]
            workflow.status = WorkflowStatus.RUNNING
            
            self.logger.info(f"开始执行工作流: {workflow_id}")
            
            # 按依赖关系执行步骤
            executed_steps = set()
            
            while len(executed_steps) < len(workflow.steps):
                # 找到可以执行的步骤
                ready_steps = []
                for step_id, step in workflow.steps.items():
                    if (step_id not in executed_steps and 
                        step.status == StepStatus.PENDING and
                        all(dep in executed_steps for dep in step.dependencies)):
                        ready_steps.append(step)
                
                if not ready_steps:
                    # 检查是否有失败的步骤
                    failed_steps = [s for s in workflow.steps.values() if s.status == StepStatus.FAILED]
                    if failed_steps:
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error_message = f"步骤失败: {', '.join(s.name for s in failed_steps)}"
                        break
                    else:
                        # 可能存在循环依赖
                        workflow.status = WorkflowStatus.FAILED
                        workflow.error_message = "工作流存在循环依赖或无法执行的步骤"
                        break
                
                # 并行执行准备好的步骤
                tasks = []
                for step in ready_steps:
                    task = asyncio.create_task(self._execute_step(workflow_id, step))
                    tasks.append(task)
                
                # 等待所有步骤完成
                await asyncio.gather(*tasks)
                
                # 更新已执行步骤
                for step in ready_steps:
                    if step.status in [StepStatus.COMPLETED, StepStatus.FAILED, StepStatus.SKIPPED]:
                        executed_steps.add(step.id)
            
            # 完成工作流
            workflow.end_time = time.time()
            workflow.total_duration = workflow.end_time - workflow.start_time
            
            if workflow.status == WorkflowStatus.RUNNING:
                workflow.status = WorkflowStatus.COMPLETED
                self.logger.info(f"工作流执行完成: {workflow_id}")
            else:
                self.logger.error(f"工作流执行失败: {workflow_id} - {workflow.error_message}")
                
        except Exception as e:
            workflow = self.active_workflows.get(workflow_id)
            if workflow:
                workflow.status = WorkflowStatus.FAILED
                workflow.error_message = str(e)
                workflow.end_time = time.time()
                workflow.total_duration = workflow.end_time - workflow.start_time
            
            self.logger.error(f"工作流执行异常 {workflow_id}: {str(e)}")
    
    async def _execute_step(self, workflow_id: str, step: WorkflowStep):
        """执行单个步骤"""
        try:
            step.status = StepStatus.RUNNING
            step.start_time = time.time()
            
            self.logger.info(f"执行步骤: {step.name} ({workflow_id})")
            
            # 获取工作流上下文
            workflow = self.active_workflows[workflow_id]
            context = getattr(workflow, 'context', {})
            
            # 执行步骤处理器
            result = await step.handler(context, step)
            
            step.result = result
            step.status = StepStatus.COMPLETED
            step.progress = 100.0
            step.end_time = time.time()
            
            self.logger.info(f"步骤完成: {step.name} ({workflow_id})")
            
        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)
            step.end_time = time.time()
            
            self.logger.error(f"步骤失败: {step.name} ({workflow_id}) - {str(e)}")
    
    async def _handle_content_generation(self, context: Dict[str, Any], step: WorkflowStep) -> VideoContent:
        """处理AI内容生成步骤"""
        topic = context['content_input']  # 这里是主题字符串
        requirements = context['requirements']
        
        # 使用AI协调器生成内容
        video_content = await self.ai_orchestrator.process_video_content(topic, requirements)
        
        # 更新上下文
        context['video_content'] = video_content
        
        return video_content
    
    async def _handle_content_preparation(self, context: Dict[str, Any], step: WorkflowStep) -> VideoContent:
        """处理用户提供内容的准备步骤"""
        content_input = context['content_input']  # 这里是内容字典
        requirements = context['requirements']
        
        # 创建VideoContent对象
        video_content = VideoContent(
            title=content_input.get('title', '未命名视频'),
            script=content_input.get('script', ''),
            language=content_input.get('language', requirements.get('language', 'zh-CN')),
            style=content_input.get('style', requirements.get('style', 'default')),
            target_duration=content_input.get('duration', requirements.get('duration', 60))
        )
        
        # 如果用户提供了翻译文本
        if content_input.get('translated_script'):
            video_content.translated_script = content_input['translated_script']
        
        # 如果用户提供了图标/图片
        if content_input.get('icons'):
            video_content.icons = content_input['icons']
        
        # 如果用户提供了音频文件
        if content_input.get('audio_file'):
            video_content.audio_file = content_input['audio_file']
        
        # 更新上下文
        context['video_content'] = video_content
        
        return video_content
    
    async def _handle_template_selection(self, context: Dict[str, Any], step: WorkflowStep) -> str:
        """处理模板选择步骤"""
        video_content = context['video_content']
        requirements = context['requirements']
        
        # 根据内容类型选择模板
        template_id = self._select_template_by_content(video_content, requirements)
        
        # 更新上下文
        context['selected_template'] = template_id
        
        return template_id
    
    def _select_template_by_content(self, video_content: VideoContent, requirements: Dict[str, Any]) -> str:
        """根据内容选择合适的模板"""
        # 简单的模板选择逻辑
        script_length = len(video_content.script)
        
        # 根据脚本长度和风格选择模板
        if script_length < 100:
            return 'simple_text'
        elif '\n' in video_content.script and script_length > 200:
            return 'list_display'
        else:
            return 'simple_text'
    
    async def _handle_parameter_preparation(self, context: Dict[str, Any], step: WorkflowStep) -> Dict[str, Any]:
        """处理参数准备步骤"""
        video_content = context['video_content']
        template_id = context['selected_template']
        requirements = context['requirements']
        
        # 获取模板参数定义
        template = self.template_manager.get_template(template_id)
        if not template:
            raise Exception(f"模板不存在: {template_id}")
        
        # 准备模板参数
        parameters = self._prepare_template_parameters(video_content, template, requirements)
        
        # 验证参数
        validated_parameters = self.template_manager.validate_template_parameters(template_id, parameters)
        
        # 更新上下文
        context['template_parameters'] = validated_parameters
        
        return validated_parameters
    
    def _prepare_template_parameters(self, video_content: VideoContent, template, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """准备模板参数"""
        parameters = {}
        
        # 基础参数映射
        if template.metadata.id == 'simple_text':
            parameters = {
                'title': video_content.title,
                'subtitle': video_content.script[:100] + '...' if len(video_content.script) > 100 else video_content.script,
                'font_size': requirements.get('font_size', 48),
                'text_color': requirements.get('text_color', 'WHITE'),
                'background_color': requirements.get('background_color', 'BLACK'),
                'animation_style': requirements.get('animation_style', 'fade')
            }
        elif template.metadata.id == 'list_display':
            parameters = {
                'title': video_content.title,
                'items': video_content.script,
                'max_items_per_screen': requirements.get('max_items_per_screen', 5),
                'item_animation': requirements.get('item_animation', 'sequential')
            }
        
        return parameters
    
    async def _handle_scene_creation(self, context: Dict[str, Any], step: WorkflowStep):
        """处理场景创建步骤"""
        template_id = context['selected_template']
        parameters = context['template_parameters']
        
        # 创建场景类
        scene_class = self.template_manager.create_scene_from_template(template_id, parameters)
        
        # 更新上下文
        context['scene_class'] = scene_class
        
        return scene_class
    
    async def _handle_video_rendering(self, context: Dict[str, Any], step: WorkflowStep) -> str:
        """处理视频渲染步骤"""
        scene_class = context['scene_class']
        requirements = context['requirements']
        
        # 创建渲染配置
        quality_map = {
            'low_quality': RenderQuality.LOW,
            'medium_quality': RenderQuality.MEDIUM,
            'high_quality': RenderQuality.HIGH,
            'production_quality': RenderQuality.PRODUCTION
        }
        
        render_config = RenderConfig(
            quality=quality_map.get(requirements.get('quality', 'medium_quality'), RenderQuality.MEDIUM),
            resolution=requirements.get('resolution', (1920, 1080)),
            frame_rate=requirements.get('frame_rate', 30),
            background_color=requirements.get('background_color', 'BLACK')
        )
        
        # 提交渲染任务
        job_id = await self.render_manager.submit_render_job(scene_class, render_config)
        
        # 等待渲染完成
        while True:
            status = self.render_manager.get_job_status(job_id)
            if not status:
                raise Exception(f"渲染任务不存在: {job_id}")
            
            step.progress = status['progress']
            
            if status['status'] == 'completed':
                context['render_job_id'] = job_id
                return status['output_file']
            elif status['status'] == 'failed':
                raise Exception(f"渲染失败: {status.get('error_message', '未知错误')}")
            
            await asyncio.sleep(2)  # 每2秒检查一次
    
    async def _handle_post_processing(self, context: Dict[str, Any], step: WorkflowStep) -> List[str]:
        """处理后期处理步骤"""
        video_content = context['video_content']
        render_job_id = context['render_job_id']
        
        output_files = []
        
        # 获取渲染结果
        job_status = self.render_manager.get_job_status(render_job_id)
        if job_status and job_status.get('output_file'):
            output_files.append(job_status['output_file'])
        
        # 如果有音频文件，可以在这里合并
        if video_content.audio_file:
            # TODO: 实现音视频合并
            pass
        
        # 生成字幕文件
        if video_content.script:
            subtitle_file = self._generate_subtitle_file(video_content.script, render_job_id)
            if subtitle_file:
                output_files.append(subtitle_file)
        
        return output_files
    
    def _generate_subtitle_file(self, script: str, job_id: str) -> Optional[str]:
        """生成字幕文件"""
        try:
            # 简单的SRT字幕生成
            subtitle_content = f"""1
00:00:01,000 --> 00:00:05,000
{script[:50]}

2
00:00:05,000 --> 00:00:10,000
{script[50:100] if len(script) > 50 else ''}
"""
            
            subtitle_file = f"output/subtitles_{job_id}.srt"
            with open(subtitle_file, 'w', encoding='utf-8') as f:
                f.write(subtitle_content)
            
            return subtitle_file
            
        except Exception as e:
            self.logger.warning(f"生成字幕文件失败: {str(e)}")
            return None
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流状态"""
        if workflow_id not in self.active_workflows:
            return None
        
        workflow = self.active_workflows[workflow_id]
        
        return {
            'id': workflow.workflow_id,
            'status': workflow.status.value,
            'start_time': workflow.start_time,
            'end_time': workflow.end_time,
            'total_duration': workflow.total_duration,
            'steps': {
                step_id: {
                    'name': step.name,
                    'status': step.status.value,
                    'progress': step.progress,
                    'error': step.error
                }
                for step_id, step in workflow.steps.items()
            },
            'output_files': workflow.output_files,
            'error_message': workflow.error_message
        }
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        if workflow_id not in self.active_workflows:
            return False
        
        workflow = self.active_workflows[workflow_id]
        
        # 取消渲染任务
        context = getattr(workflow, 'context', {})
        if context.get('render_job_id'):
            self.render_manager.cancel_job(context['render_job_id'])
        
        # 更新状态
        workflow.status = WorkflowStatus.CANCELLED
        workflow.end_time = time.time()
        workflow.total_duration = workflow.end_time - workflow.start_time
        
        self.logger.info(f"工作流已取消: {workflow_id}")
        return True
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """列出活跃的工作流"""
        return [
            {
                'id': workflow_id,
                'status': workflow.status.value,
                'start_time': workflow.start_time,
                'total_duration': workflow.total_duration
            }
            for workflow_id, workflow in self.active_workflows.items()
            if workflow.status in [WorkflowStatus.CREATED, WorkflowStatus.RUNNING]
        ]
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24):
        """清理已完成的工作流"""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)
        
        to_remove = []
        for workflow_id, workflow in self.active_workflows.items():
            if (workflow.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                workflow.end_time and workflow.end_time < cutoff_time):
                to_remove.append(workflow_id)
        
        for workflow_id in to_remove:
            del self.active_workflows[workflow_id]
        
        if to_remove:
            self.logger.info(f"清理了 {len(to_remove)} 个已完成的工作流")
