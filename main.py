"""
ClipTurbo Main Application Entry Point
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Dict, Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import yaml
from dotenv import load_dotenv

from src.ai_services import AIOrchestrator
from src.manim_engine import TemplateManager, RenderManager
from src.core import ProjectManager, WorkflowEngine


# Load environment variables
load_dotenv()

# Load configuration
def load_config() -> Dict[str, Any]:
    """加载配置文件"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError("配置文件 config.yaml 不存在")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

# Initialize configuration
config = load_config()

# Setup logging
def setup_logging():
    """设置日志"""
    log_config = config.get('logging', {})
    
    # Create logs directory
    log_file = Path(log_config.get('file', './logs/clipturbo.log'))
    log_file.parent.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_config.get('level', 'INFO')),
        format=log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title=config['app']['name'],
    version=config['app']['version'],
    description="AI驱动的短视频生成工具"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config['security']['allowed_origins'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global components
ai_orchestrator: AIOrchestrator = None
template_manager: TemplateManager = None
render_manager: RenderManager = None
project_manager: ProjectManager = None
workflow_engine: WorkflowEngine = None


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global ai_orchestrator, template_manager, render_manager, project_manager, workflow_engine
    
    logger.info("正在启动 ClipTurbo...")
    
    try:
        # Initialize AI Orchestrator
        ai_config = config.get('ai_services', {})
        ai_orchestrator = AIOrchestrator(ai_config)
        logger.info("AI协调器初始化完成")
        
        # Initialize Template Manager
        template_config = config.get('manim_engine', {}).get('template_system', {})
        template_manager = TemplateManager(
            template_directory=template_config.get('template_directory')
        )
        logger.info("模板管理器初始化完成")
        
        # Initialize Render Manager
        render_config = config.get('manim_engine', {}).get('render_manager', {})
        render_manager = RenderManager(render_config)
        logger.info("渲染管理器初始化完成")
        
        # Initialize Project Manager
        project_config = config.get('project_manager', {})
        project_manager = ProjectManager(
            projects_dir=project_config.get('projects_dir', './projects')
        )
        logger.info("项目管理器初始化完成")
        
        # Initialize Workflow Engine
        workflow_engine = WorkflowEngine(
            ai_orchestrator=ai_orchestrator,
            template_manager=template_manager,
            render_manager=render_manager
        )
        logger.info("工作流引擎初始化完成")
        
        # Create necessary directories
        for directory in ['./output', './temp', './uploads', './logs']:
            Path(directory).mkdir(exist_ok=True)
        
        logger.info("ClipTurbo 启动完成!")
        
    except Exception as e:
        logger.error(f"启动失败: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("正在关闭 ClipTurbo...")
    
    if render_manager:
        await render_manager.shutdown()
    
    logger.info("ClipTurbo 已关闭")


# API Routes
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "欢迎使用 ClipTurbo!",
        "version": config['app']['version'],
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "ai_orchestrator": ai_orchestrator.get_processing_status() if ai_orchestrator else None,
            "template_manager": len(template_manager.list_templates()) if template_manager else 0,
            "render_manager": render_manager.get_queue_status() if render_manager else None,
            "project_manager": project_manager.get_project_statistics() if project_manager else None
        }
    }


# Project Management Routes
@app.post("/api/projects")
async def create_project(project_data: dict):
    """创建项目"""
    try:
        project_id = project_manager.create_project(
            name=project_data['name'],
            description=project_data.get('description', ''),
            template_id=project_data.get('template_id', 'simple_text')
        )
        return {"project_id": project_id, "message": "项目创建成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/projects")
async def list_projects(status: str = None):
    """列出项目"""
    return project_manager.list_projects(status=status)


@app.get("/api/projects/{project_id}")
async def get_project(project_id: str):
    """获取项目详情"""
    project = project_manager.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


@app.put("/api/projects/{project_id}")
async def update_project(project_id: str, updates: dict):
    """更新项目"""
    success = project_manager.update_project(project_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在或更新失败")
    return {"message": "项目更新成功"}


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: str):
    """删除项目"""
    success = project_manager.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="项目不存在")
    return {"message": "项目删除成功"}


# Template Management Routes
@app.get("/api/templates")
async def list_templates(category: str = None):
    """列出模板"""
    return template_manager.list_templates(category=category)


@app.get("/api/templates/{template_id}")
async def get_template_info(template_id: str):
    """获取模板信息"""
    template = template_manager.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    return template_manager.export_template_config(template_id)


@app.get("/api/templates/{template_id}/parameters")
async def get_template_parameters(template_id: str):
    """获取模板参数"""
    try:
        parameters = template_manager.get_template_parameters(template_id)
        return {"parameters": [param.__dict__ for param in parameters]}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Video Generation Routes
@app.post("/api/generate")
async def generate_video(generation_request: dict):
    """生成视频"""
    try:
        # 支持两种模式：
        # 1. AI生成模式：传入topic字符串
        # 2. 直接内容模式：传入完整的content对象
        content_input = generation_request.get('topic') or generation_request.get('content')
        
        if not content_input:
            raise HTTPException(status_code=400, detail="必须提供topic或content参数")
        
        workflow_id = await workflow_engine.create_video_workflow(
            content_input=content_input,
            requirements=generation_request.get('requirements', {})
        )
        return {"workflow_id": workflow_id, "message": "视频生成任务已启动"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/generate/with-content")
async def generate_video_with_content(generation_request: dict):
    """使用用户提供的内容生成视频"""
    try:
        required_fields = ['title', 'script']
        content = generation_request.get('content', {})
        
        # 验证必需字段
        missing_fields = [field for field in required_fields if not content.get(field)]
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"缺少必需字段: {', '.join(missing_fields)}"
            )
        
        workflow_id = await workflow_engine.create_video_workflow(
            content_input=content,
            requirements=generation_request.get('requirements', {})
        )
        return {"workflow_id": workflow_id, "message": "视频生成任务已启动"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/workflows/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """获取工作流状态"""
    status = workflow_engine.get_workflow_status(workflow_id)
    if not status:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return status


@app.post("/api/workflows/{workflow_id}/cancel")
async def cancel_workflow(workflow_id: str):
    """取消工作流"""
    success = workflow_engine.cancel_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="工作流不存在")
    return {"message": "工作流已取消"}


@app.get("/api/workflows")
async def list_active_workflows():
    """列出活跃的工作流"""
    return workflow_engine.list_active_workflows()


# Render Management Routes
@app.get("/api/render/queue")
async def get_render_queue():
    """获取渲染队列状态"""
    return render_manager.get_queue_status()


@app.get("/api/render/jobs/{job_id}")
async def get_render_job_status(job_id: str):
    """获取渲染任务状态"""
    status = render_manager.get_job_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="渲染任务不存在")
    return status


@app.post("/api/render/jobs/{job_id}/cancel")
async def cancel_render_job(job_id: str):
    """取消渲染任务"""
    success = render_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="渲染任务不存在")
    return {"message": "渲染任务已取消"}


# System Information Routes
@app.get("/api/system/resources")
async def get_system_resources():
    """获取系统资源信息"""
    return render_manager.get_system_resources()


@app.get("/api/system/config")
async def get_system_config():
    """获取系统配置信息"""
    # 返回非敏感的配置信息
    safe_config = {
        "app": config["app"],
        "manim_engine": {
            "render_manager": {
                k: v for k, v in config["manim_engine"]["render_manager"].items()
                if k not in ["temp_dir"]
            }
        },
        "project_manager": config["project_manager"],
        "performance": config["performance"]
    }
    return safe_config


# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/output", StaticFiles(directory="output"), name="output")


def main():
    """主函数"""
    app_config = config.get('app', {})
    
    uvicorn.run(
        "main:app",
        host=app_config.get('host', '0.0.0.0'),
        port=app_config.get('port', 8000),
        reload=app_config.get('debug', False),
        log_level=config.get('logging', {}).get('level', 'info').lower()
    )


if __name__ == "__main__":
    main()
