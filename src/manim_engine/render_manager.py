"""
Render Manager - Manim渲染管理器
"""

import asyncio
import subprocess
import tempfile
import shutil
import inspect
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging
import json
import time
import psutil

from manim import Scene, config as manim_config


class RenderQuality(Enum):
    """渲染质量枚举"""
    LOW = "low_quality"
    MEDIUM = "medium_quality"
    HIGH = "high_quality"
    PRODUCTION = "production_quality"


class RenderStatus(Enum):
    """渲染状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class RenderConfig:
    """渲染配置"""
    quality: RenderQuality = RenderQuality.MEDIUM
    resolution: tuple = (1920, 1080)  # 分辨率
    frame_rate: int = 30  # 帧率
    aspect_ratio: str = "16:9"  # 宽高比
    background_color: str = "BLACK"  # 背景颜色
    output_format: str = "mp4"  # 输出格式
    audio_enabled: bool = True  # 是否包含音频
    preview_mode: bool = False  # 预览模式（低质量快速渲染）
    custom_flags: List[str] = field(default_factory=list)  # 自定义manim参数


@dataclass
class RenderJob:
    """渲染任务"""
    id: str
    scene_class: type
    scene_file: str
    config: RenderConfig
    output_path: str
    status: RenderStatus = RenderStatus.PENDING
    progress: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    error_message: Optional[str] = None
    process: Optional[subprocess.Popen] = None


@dataclass
class RenderResult:
    """渲染结果"""
    job_id: str
    success: bool
    output_file: str
    duration: float
    file_size: int
    resolution: tuple
    frame_count: int
    error_message: Optional[str] = None


class RenderManager:
    """渲染管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 渲染队列和任务
        self.render_queue: List[RenderJob] = []
        self.active_jobs: Dict[str, RenderJob] = {}
        self.completed_jobs: Dict[str, RenderResult] = {}
        
        # 并发控制
        self.max_concurrent_renders = config.get('max_concurrent_renders', 2)
        self.current_renders = 0
        
        # 输出目录
        self.output_dir = Path(config.get('output_dir', './output'))
        self.output_dir.mkdir(exist_ok=True)
        
        # 临时目录
        self.temp_dir = Path(config.get('temp_dir', tempfile.gettempdir())) / 'clipturbo_render'
        self.temp_dir.mkdir(exist_ok=True)
        
        # 质量预设
        self.quality_presets = {
            RenderQuality.LOW: {
                'pixel_height': 480,
                'pixel_width': 854,
                'frame_rate': 15,
                'quality': 'low_quality'
            },
            RenderQuality.MEDIUM: {
                'pixel_height': 720,
                'pixel_width': 1280,
                'frame_rate': 24,
                'quality': 'medium_quality'
            },
            RenderQuality.HIGH: {
                'pixel_height': 1080,
                'pixel_width': 1920,
                'frame_rate': 30,
                'quality': 'high_quality'
            },
            RenderQuality.PRODUCTION: {
                'pixel_height': 1080,
                'pixel_width': 1920,
                'frame_rate': 60,
                'quality': 'production_quality'
            }
        }
        
        # 启动渲染监控
        self._monitoring_task = None
        self._start_monitoring()
    
    def _start_monitoring(self):
        """启动渲染监控任务"""
        if self._monitoring_task is None:
            self._monitoring_task = asyncio.create_task(self._monitor_renders())
    
    async def _monitor_renders(self):
        """监控渲染进程"""
        while True:
            try:
                # 检查活跃任务状态
                for job_id, job in list(self.active_jobs.items()):
                    if job.process:
                        # 检查进程是否完成
                        if job.process.poll() is not None:
                            await self._handle_job_completion(job)
                        else:
                            # 更新进度
                            self._update_job_progress(job)
                
                # 启动新的渲染任务
                await self._start_pending_jobs()
                
                await asyncio.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                self.logger.error(f"渲染监控错误: {str(e)}")
                await asyncio.sleep(5)
    
    async def submit_render_job(
        self,
        scene_class: type,
        config: RenderConfig,
        job_id: Optional[str] = None
    ) -> str:
        """提交渲染任务"""
        if job_id is None:
            job_id = f"render_{int(time.time() * 1000)}"
        
        # 创建场景文件
        scene_file = await self._create_scene_file(scene_class, job_id)
        
        # 生成输出路径
        output_filename = f"{job_id}.{config.output_format}"
        output_path = str(self.output_dir / output_filename)
        
        # 创建渲染任务
        job = RenderJob(
            id=job_id,
            scene_class=scene_class,
            scene_file=scene_file,
            config=config,
            output_path=output_path
        )
        
        # 添加到队列
        self.render_queue.append(job)
        
        self.logger.info(f"渲染任务已提交: {job_id}")
        return job_id
    
    async def _create_scene_file(self, scene_class: type, job_id: str) -> str:
        """创建场景文件"""
        scene_file = self.temp_dir / f"scene_{job_id}.py"
        
        # 生成场景文件内容
        scene_code = f'''
from manim import *

class RenderScene(Scene):
    def construct(self):
        # 动态创建的场景
        scene_instance = {scene_class.__name__}()
        scene_instance.construct()

# 将场景类复制到文件中
{inspect.getsource(scene_class)}
'''
        
        # 写入文件
        with open(scene_file, 'w', encoding='utf-8') as f:
            f.write(scene_code)
        
        return str(scene_file)
    
    async def _start_pending_jobs(self):
        """启动待处理的任务"""
        while (self.current_renders < self.max_concurrent_renders and 
               self.render_queue):
            
            job = self.render_queue.pop(0)
            await self._start_render_job(job)
    
    async def _start_render_job(self, job: RenderJob):
        """启动单个渲染任务"""
        try:
            job.status = RenderStatus.RUNNING
            job.start_time = time.time()
            self.active_jobs[job.id] = job
            self.current_renders += 1
            
            # 构建manim命令
            cmd = self._build_manim_command(job)
            
            # 启动渲染进程
            job.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.temp_dir
            )
            
            self.logger.info(f"开始渲染任务: {job.id}")
            
        except Exception as e:
            job.status = RenderStatus.FAILED
            job.error_message = str(e)
            self.logger.error(f"启动渲染任务失败 {job.id}: {str(e)}")
            await self._handle_job_completion(job)
    
    def _build_manim_command(self, job: RenderJob) -> List[str]:
        """构建manim命令"""
        config = job.config
        quality_preset = self.quality_presets[config.quality.value]
        
        cmd = [
            'manim',
            job.scene_file,
            'RenderScene',  # 场景类名
            f'--quality={quality_preset["quality"]}',
            f'--resolution={config.resolution[0]},{config.resolution[1]}',
            f'--frame_rate={config.frame_rate}',
            f'--output_file={job.output_path}',
        ]
        
        # 预览模式
        if config.preview_mode:
            cmd.append('--preview')
        
        # 背景颜色
        if config.background_color:
            cmd.append(f'--background_color={config.background_color}')
        
        # 自定义参数
        cmd.extend(config.custom_flags)
        
        return cmd
    
    def _update_job_progress(self, job: RenderJob):
        """更新任务进度"""
        try:
            if job.process and job.process.stdout:
                # 简单的进度估算（基于运行时间）
                if job.start_time:
                    elapsed = time.time() - job.start_time
                    # 假设平均渲染时间为30秒
                    estimated_total = 30
                    progress = min(elapsed / estimated_total * 100, 95)
                    job.progress = progress
        except Exception as e:
            self.logger.warning(f"更新进度失败 {job.id}: {str(e)}")
    
    async def _handle_job_completion(self, job: RenderJob):
        """处理任务完成"""
        try:
            job.end_time = time.time()
            
            if job.process:
                return_code = job.process.returncode
                stdout, stderr = job.process.communicate()
                
                if return_code == 0:
                    # 渲染成功
                    job.status = RenderStatus.COMPLETED
                    job.progress = 100.0
                    
                    # 创建结果对象
                    result = await self._create_render_result(job)
                    self.completed_jobs[job.id] = result
                    
                    self.logger.info(f"渲染完成: {job.id}")
                else:
                    # 渲染失败
                    job.status = RenderStatus.FAILED
                    job.error_message = stderr or "渲染进程异常退出"
                    
                    result = RenderResult(
                        job_id=job.id,
                        success=False,
                        output_file="",
                        duration=0,
                        file_size=0,
                        resolution=(0, 0),
                        frame_count=0,
                        error_message=job.error_message
                    )
                    self.completed_jobs[job.id] = result
                    
                    self.logger.error(f"渲染失败 {job.id}: {job.error_message}")
            
            # 清理
            if job.id in self.active_jobs:
                del self.active_jobs[job.id]
            self.current_renders -= 1
            
            # 清理临时文件
            self._cleanup_job_files(job)
            
        except Exception as e:
            self.logger.error(f"处理任务完成时出错 {job.id}: {str(e)}")
    
    async def _create_render_result(self, job: RenderJob) -> RenderResult:
        """创建渲染结果"""
        output_file = Path(job.output_path)
        
        if output_file.exists():
            file_size = output_file.stat().st_size
            duration = job.end_time - job.start_time if job.start_time else 0
            
            # 获取视频信息（简单实现）
            resolution = job.config.resolution
            frame_count = 0  # 需要使用ffprobe等工具获取准确信息
            
            return RenderResult(
                job_id=job.id,
                success=True,
                output_file=str(output_file),
                duration=duration,
                file_size=file_size,
                resolution=resolution,
                frame_count=frame_count
            )
        else:
            raise Exception(f"输出文件不存在: {job.output_path}")
    
    def _cleanup_job_files(self, job: RenderJob):
        """清理任务文件"""
        try:
            # 删除临时场景文件
            scene_file = Path(job.scene_file)
            if scene_file.exists():
                scene_file.unlink()
            
            # 清理其他临时文件
            temp_pattern = f"*{job.id}*"
            for temp_file in self.temp_dir.glob(temp_pattern):
                if temp_file.is_file():
                    temp_file.unlink()
                    
        except Exception as e:
            self.logger.warning(f"清理临时文件失败 {job.id}: {str(e)}")
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        # 检查活跃任务
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            return {
                'id': job.id,
                'status': job.status.value,
                'progress': job.progress,
                'start_time': job.start_time,
                'error_message': job.error_message
            }
        
        # 检查已完成任务
        if job_id in self.completed_jobs:
            result = self.completed_jobs[job_id]
            return {
                'id': result.job_id,
                'status': 'completed' if result.success else 'failed',
                'progress': 100.0 if result.success else 0.0,
                'output_file': result.output_file,
                'duration': result.duration,
                'file_size': result.file_size,
                'error_message': result.error_message
            }
        
        # 检查队列中的任务
        for job in self.render_queue:
            if job.id == job_id:
                return {
                    'id': job.id,
                    'status': job.status.value,
                    'progress': 0.0,
                    'start_time': None,
                    'error_message': None
                }
        
        return None
    
    def cancel_job(self, job_id: str) -> bool:
        """取消任务"""
        # 取消活跃任务
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.process:
                try:
                    job.process.terminate()
                    job.status = RenderStatus.CANCELLED
                    return True
                except Exception as e:
                    self.logger.error(f"取消任务失败 {job_id}: {str(e)}")
                    return False
        
        # 从队列中移除
        for i, job in enumerate(self.render_queue):
            if job.id == job_id:
                job.status = RenderStatus.CANCELLED
                self.render_queue.pop(i)
                return True
        
        return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        return {
            'pending_jobs': len(self.render_queue),
            'active_jobs': len(self.active_jobs),
            'completed_jobs': len(self.completed_jobs),
            'max_concurrent': self.max_concurrent_renders,
            'current_renders': self.current_renders
        }
    
    def clear_completed_jobs(self):
        """清理已完成的任务记录"""
        self.completed_jobs.clear()
        self.logger.info("已清理完成任务记录")
    
    async def render_preview(
        self,
        scene_class: type,
        config: Optional[RenderConfig] = None
    ) -> str:
        """快速预览渲染"""
        if config is None:
            config = RenderConfig(
                quality=RenderQuality.LOW,
                preview_mode=True,
                resolution=(640, 360)
            )
        else:
            config.preview_mode = True
            config.quality = RenderQuality.LOW
        
        job_id = f"preview_{int(time.time() * 1000)}"
        return await self.submit_render_job(scene_class, config, job_id)
    
    def get_system_resources(self) -> Dict[str, Any]:
        """获取系统资源使用情况"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(str(self.output_dir))
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_gb': memory.available / (1024**3),
                'disk_free_gb': disk.free / (1024**3),
                'active_renders': self.current_renders,
                'max_renders': self.max_concurrent_renders
            }
        except Exception as e:
            self.logger.error(f"获取系统资源信息失败: {str(e)}")
            return {}
    
    async def shutdown(self):
        """关闭渲染管理器"""
        self.logger.info("正在关闭渲染管理器...")
        
        # 取消所有活跃任务
        for job_id in list(self.active_jobs.keys()):
            self.cancel_job(job_id)
        
        # 停止监控任务
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        
        # 清理临时目录
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            self.logger.warning(f"清理临时目录失败: {str(e)}")
        
        self.logger.info("渲染管理器已关闭")
