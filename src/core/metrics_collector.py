"""
System Metrics and Performance Monitoring Module
"""

import time
import threading
import psutil
import asyncio
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json


@dataclass
class SystemMetrics:
    """系统性能指标"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used: int  # MB
    memory_total: int  # MB
    disk_usage_percent: float
    disk_used: int  # GB
    disk_total: int  # GB
    network_bytes_sent: int
    network_bytes_recv: int
    active_render_jobs: int
    active_workflows: int
    api_requests_count: int
    error_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp,
            'cpu_percent': self.cpu_percent,
            'memory_percent': self.memory_percent,
            'memory_used': self.memory_used,
            'memory_total': self.memory_total,
            'disk_usage_percent': self.disk_usage_percent,
            'disk_used': self.disk_used,
            'disk_total': self.disk_total,
            'network_bytes_sent': self.network_bytes_sent,
            'network_bytes_recv': self.network_bytes_recv,
            'active_render_jobs': self.active_render_jobs,
            'active_workflows': self.active_workflows,
            'api_requests_count': self.api_requests_count,
            'error_count': self.error_count
        }


@dataclass
class PerformanceMetrics:
    """性能指标"""
    start_time: float
    end_time: float
    duration: float  # 秒
    success: bool
    error_message: Optional[str] = None
    steps_completed: int = 0
    total_steps: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'start_time': self.start_time,
            'end_time': self.end_time,
            'duration': self.duration,
            'success': self.success,
            'error_message': self.error_message,
            'steps_completed': self.steps_completed,
            'total_steps': self.total_steps,
            'completion_rate': (self.steps_completed / self.total_steps * 100) if self.total_steps > 0 else 0
        }


class MetricsCollector:
    """性能指标收集器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # 存储路径
        self.metrics_dir = Path(config.get('metrics_dir', './metrics'))
        self.metrics_dir.mkdir(exist_ok=True)
        
        # 历史数据
        self.system_metrics_history: List[SystemMetrics] = []
        self.performance_metrics_history: List[PerformanceMetrics] = []
        
        # 当前状态
        self.current_system_metrics: Optional[SystemMetrics] = None
        self.api_requests_count = 0
        self.error_count = 0
        
        # 引用外部服务
        self.render_manager_ref = None
        self.workflow_engine_ref = None
        
        # 监控线程
        self.monitoring_thread = None
        self.is_monitoring = False
        
        # 性能回调
        self.performance_callbacks: List[Callable[[PerformanceMetrics], None]] = []
        
        # 指标收集间隔
        self.collect_interval = config.get('collect_interval', 30)  # 秒
        self.history_limit = config.get('history_limit', 1000)  # 保存条数
        
    def set_service_refs(self, render_manager=None, workflow_engine=None):
        """设置服务引用"""
        self.render_manager_ref = render_manager
        self.workflow_engine_ref = workflow_engine
    
    async def collect_system_metrics(self) -> SystemMetrics:
        """收集系统性能指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 内存使用
            memory = psutil.virtual_memory()
            memory_used = int(memory.used / 1024 / 1024)  # MB
            memory_total = int(memory.total / 1024 / 1024)  # MB
            memory_percent = memory.percent
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            disk_used = int(disk.used / 1024 / 1024 / 1024)  # GB
            disk_total = int(disk.total / 1024 / 1024 / 1024)  # GB
            disk_usage_percent = disk.percent
            
            # 网络统计
            net_io = psutil.net_io_counters()
            network_bytes_sent = net_io.bytes_sent
            network_bytes_recv = net_io.bytes_recv
            
            # 活跃任务
            active_render_jobs = 0
            if self.render_manager_ref:
                active_render_jobs = len(self.render_manager_ref.current_renders)
            
            active_workflows = 0
            if self.workflow_engine_ref:
                # 需要从workflow_engine获取活跃工作流数量
                active_workflows = len(getattr(self.workflow_engine_ref, 'active_workflows', {}))
            
            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used=memory_used,
                memory_total=memory_total,
                disk_usage_percent=disk_usage_percent,
                disk_used=disk_used,
                disk_total=disk_total,
                network_bytes_sent=network_bytes_sent,
                network_bytes_recv=network_bytes_recv,
                active_render_jobs=active_render_jobs,
                active_workflows=active_workflows,
                api_requests_count=self.api_requests_count,
                error_count=self.error_count
            )
            
            self.current_system_metrics = metrics
            return metrics
            
        except Exception as e:
            self.logger.error(f"收集系统指标失败: {str(e)}")
            return None
    
    async def record_performance_metrics(self, performance_metrics: PerformanceMetrics):
        """记录性能指标"""
        try:
            self.performance_metrics_history.append(performance_metrics)
            
            # 限制历史记录数量
            if len(self.performance_metrics_history) > self.history_limit:
                self.performance_metrics_history = self.performance_metrics_history[-self.history_limit:]
            
            # 调用性能回调
            for callback in self.performance_callbacks:
                try:
                    callback(performance_metrics)
                except Exception as e:
                    self.logger.error(f"性能回调执行失败: {str(e)}")
            
            self.logger.info(f"记录性能指标: {performance_metrics}")
            
        except Exception as e:
            self.logger.error(f"记录性能指标失败: {str(e)}")
    
    def increment_api_requests(self):
        """增加API请求计数"""
        self.api_requests_count += 1
    
    def increment_error_count(self):
        """增加错误计数"""
        self.error_count += 1
    
    def add_performance_callback(self, callback: Callable[[PerformanceMetrics], None]):
        """添加性能回调"""
        self.performance_callbacks.append(callback)
    
    def start_monitoring(self):
        """启动监控"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        self.logger.info("系统监控已启动")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        self.logger.info("系统监控已停止")
    
    def _monitoring_loop(self):
        """监控循环"""
        while self.is_monitoring:
            try:
                # 收集系统指标
                loop = asyncio.new_event_loop()
                try:
                    metrics = loop.run_until_complete(self.collect_system_metrics())
                finally:
                    loop.close()
                
                if metrics:
                    # 保存历史记录
                    self.system_metrics_history.append(metrics)
                    
                    # 限制历史记录数量
                    if len(self.system_metrics_history) > self.history_limit:
                        self.system_metrics_history = self.system_metrics_history[-self.history_limit:]
                    
                    # 保存到文件
                    self._save_metrics_to_file(metrics)
                    
                # 等待下次收集
                time.sleep(self.collect_interval)
                
            except Exception as e:
                self.logger.error(f"监控循环错误: {str(e)}")
                time.sleep(5)  # 错误时等待5秒
    
    def _save_metrics_to_file(self, metrics: SystemMetrics):
        """保存指标到文件"""
        try:
            # 按日期保存
            date_str = datetime.fromtimestamp(metrics.timestamp).strftime('%Y-%m-%d')
            filename = f"system_metrics_{date_str}.json"
            filepath = self.metrics_dir / filename
            
            # 读取现有数据
            existing_data = []
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            
            # 添加新数据
            existing_data.append(metrics.to_dict())
            
            # 保存回文件
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"保存指标文件失败: {str(e)}")
    
    def get_system_metrics_history(self, 
                               hours: int = 24,
                               limit: int = 100) -> List[SystemMetrics]:
        """获取系统指标历史"""
        cutoff_time = time.time() - (hours * 3600)
        
        # 过滤数据
        filtered = [
            m for m in self.system_metrics_history 
            if m.timestamp >= cutoff_time
        ]
        
        # 限制数量并返回
        return filtered[-limit:] if limit else filtered
    
    def get_performance_metrics_history(self,
                                       hours: int = 24,
                                       limit: int = 100) -> List[PerformanceMetrics]:
        """获取性能指标历史"""
        cutoff_time = time.time() - (hours * 3600)
        
        # 过滤数据
        filtered = [
            p for p in self.performance_metrics_history 
            if p.start_time >= cutoff_time
        ]
        
        # 限制数量并返回
        return filtered[-limit:] if limit else filtered
    
    def get_current_stats(self) -> Dict[str, Any]:
        """获取当前统计信息"""
        if not self.current_system_metrics:
            return {}
        
        return {
            'system_metrics': self.current_system_metrics.to_dict(),
            'api_requests_count': self.api_requests_count,
            'error_count': self.error_count,
            'system_history_count': len(self.system_metrics_history),
            'performance_history_count': len(self.performance_metrics_history),
            'monitoring_active': self.is_monitoring
        }
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """获取性能摘要"""
        perf_metrics = self.get_performance_metrics_history(hours=hours)
        sys_metrics = self.get_system_metrics_history(hours=hours)
        
        if not perf_metrics:
            return {}
        
        # 计算统计信息
        total_requests = len(perf_metrics)
        successful_requests = sum(1 for p in perf_metrics if p.success)
        failed_requests = total_requests - successful_requests
        success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
        
        # 平均耗时
        avg_duration = sum(p.duration for p in perf_metrics) / total_requests if total_requests > 0 else 0
        
        # 系统资源平均使用率
        if sys_metrics:
            avg_cpu = sum(m.cpu_percent for m in sys_metrics) / len(sys_metrics)
            avg_memory = sum(m.memory_percent for m in sys_metrics) / len(sys_metrics)
            avg_disk = sum(m.disk_usage_percent for m in sys_metrics) / len(sys_metrics)
        else:
            avg_cpu = avg_memory = avg_disk = 0
        
        return {
            'time_period_hours': hours,
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'failed_requests': failed_requests,
            'success_rate': success_rate,
            'average_duration_seconds': avg_duration,
            'average_cpu_usage': avg_cpu,
            'average_memory_usage': avg_memory,
            'average_disk_usage': avg_disk,
            'timestamp': datetime.now().isoformat()
        }
    
    def export_metrics_report(self, hours: int = 24, output_path: Optional[str] = None):
        """导出指标报告"""
        try:
            summary = self.get_performance_summary(hours=hours)
            perf_metrics = self.get_performance_metrics_history(hours=hours)
            sys_metrics = self.get_system_metrics_history(hours=hours)
            
            report = {
                'summary': summary,
                'performance_metrics': [p.to_dict() for p in perf_metrics],
                'system_metrics': [m.to_dict() for m in sys_metrics],
                'generated_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }
            
            output_file = output_path or f"metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"指标报告已导出到: {output_file}")
            return output_file
            
        except Exception as e:
            self.logger.error(f"导出指标报告失败: {str(e)}")
            return None