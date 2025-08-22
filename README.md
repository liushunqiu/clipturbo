<div align="center">
  <a href="https://github.com/clipturbo/clipturbo">
    <img src="./assets/logo.svg" alt="Logo" width="80" height="80">
  </a>

  <h3>ClipTurbo 小视频宝</h3>

  <p>
    🚀 AI 驱动的短视频宝藏工具 - 灵活，快速，易于变现。
    <br />
    <br />
    <a href="https://clipturbo.himrr.com/">Website</a>
    ·
    <a href="https://sanhua.himrr.com/sanhua-wx-qrcode.jpg">Wechat</a>
    ·
    <a href="https://twitter.com/intent/follow?screen_name=yrmkejun">X</a>
    ·
    <a href="https://github.com/clipturbo/clipturbo/releases">Releases</a>
  </p>
</div>

## 关于

小视频宝(ClipTurbo)，一个易于使用的由 AI 驱动短视频生成工具，旨在帮助每个人成为吸粉短视频创作达人，让你的视频轻松变现。

**AI**: 我们利用 AI 为你处理文案、翻译、图标匹配、TTS 语音合成，最终使用 [manim](https://docs.manim.community/) 来渲染视频，告别纯生成式 AI 被平台限流的问题。

**模板**: 得益于 manim，每个 Scene 都可以是一个模板，我们正在努力提供更多模板。

**支持的平台**: 现在我们的第一优先级是 Windows 系统，稍晚一些会推出 MacOS 客户端，此外我们还有一个即将上线的 [Web版](https://clipturbo.himrr.com/?utm_source=github&utm_medium=readme)，更多模版陆续推出中。

## 🚀 快速开始

### 环境要求

- Python 3.9+
- FFmpeg
- Redis (可选，用于缓存)
- PostgreSQL (可选，默认使用SQLite)

### 安装步骤

1. **克隆仓库**
```bash
git clone https://github.com/clipturbo/clipturbo.git
cd clipturbo
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，填入你的API密钥
```

4. **启动应用**
```bash
python main.py
```

5. **访问应用**
打开浏览器访问 `http://localhost:8000`

### Docker 部署

```bash
# 使用 Docker Compose 一键部署
docker-compose up -d
```

## 🏗️ 系统架构

ClipTurbo 采用分层架构设计，包含以下核心模块：

### AI 服务层
- **内容生成**: 支持 OpenAI GPT、本地模型
- **翻译服务**: 集成 Google Translate、百度翻译、DeepL
- **图标匹配**: 支持 Unsplash、Pexels、本地素材库
- **TTS 语音**: 集成 EdgeTTS、Azure、火山云等

### 渲染引擎层
- **Manim 核心**: 基于 Manim 的视频渲染引擎
- **模板系统**: 灵活的模板管理和自定义
- **渲染管理**: 队列化渲染，支持并发处理

### 业务逻辑层
- **项目管理**: 完整的项目生命周期管理
- **工作流引擎**: 自动化的视频生成流程
- **资源管理**: 统一的资源文件管理

## 📖 API 文档

启动应用后，访问 `http://localhost:8000/docs` 查看完整的 API 文档。

### 主要 API 端点

- `POST /api/generate` - 生成视频
- `GET /api/templates` - 获取模板列表
- `POST /api/projects` - 创建项目
- `GET /api/workflows/{id}` - 查看工作流状态

## 🎨 模板系统

ClipTurbo 提供了灵活的模板系统，支持：

### 内置模板
- **简单文本**: 基础的文本展示模板
- **列表展示**: 适合展示要点、步骤的模板
- **更多模板**: 持续添加中...

### 自定义模板
```python
from src.manim_engine import VideoTemplate, TemplateMetadata

class MyCustomTemplate(VideoTemplate):
    def get_metadata(self):
        return TemplateMetadata(
            id="my_template",
            name="我的模板",
            description="自定义模板描述",
            category="custom"
        )
    
    def create_scene(self, params):
        # 实现你的场景逻辑
        pass
```

## 🔧 配置说明

主要配置文件：
- `config.yaml` - 应用主配置
- `.env` - 环境变量和API密钥
- `requirements.txt` - Python依赖

### 重要配置项

```yaml
# AI服务配置
ai_services:
  content_generator:
    openai:
      api_key: "${OPENAI_API_KEY}"
      model: "gpt-3.5-turbo"

# 渲染配置
manim_engine:
  render_manager:
    max_concurrent_renders: 2
    output_dir: "./output/videos"
```

## 📊 使用示例

### 1. 生成简单文本视频

```python
import requests

response = requests.post("http://localhost:8000/api/generate", json={
    "topic": "如何学习Python",
    "requirements": {
        "style": "educational",
        "duration": 30,
        "template_id": "simple_text"
    }
})

workflow_id = response.json()["workflow_id"]
```

### 2. 查看生成进度

```python
status = requests.get(f"http://localhost:8000/api/workflows/{workflow_id}")
print(status.json())
```

## 🛠️ 开发指南

### 项目结构
```
clipturbo/
├── src/
│   ├── ai_services/          # AI服务模块
│   ├── manim_engine/         # Manim渲染引擎
│   └── core/                 # 核心业务逻辑
├── templates/                # 视频模板
├── config.yaml              # 配置文件
├── main.py                   # 应用入口
└── requirements.txt          # 依赖列表
```

### 添加新的AI服务

1. 在 `src/ai_services/` 下创建新的服务模块
2. 继承相应的抽象基类
3. 在配置文件中添加服务配置
4. 在 `AIOrchestrator` 中集成新服务

### 创建新模板

1. 继承 `VideoTemplate` 基类
2. 实现必要的方法
3. 将模板文件放在 `templates/` 目录下
4. 重启应用自动加载

## 🤝 贡献指南

我们欢迎社区贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- 🎉 首个正式版本发布
- ✨ 完整的AI驱动视频生成流程
- 🎨 内置多种视频模板
- 🔧 灵活的配置系统
- 📊 完整的API文档

## 🐛 问题反馈

如果你遇到问题或有建议，请：

1. 查看 [FAQ](https://github.com/clipturbo/clipturbo/wiki/FAQ)
2. 搜索现有的 [Issues](https://github.com/clipturbo/clipturbo/issues)
3. 创建新的 Issue 并提供详细信息

## 📄 许可证

本项目采用 [GNU General Public License v3.0](LICENSE) 许可证。

## 🙏 致谢

感谢以下开源项目：
- [Manim](https://github.com/ManimCommunity/manim) - 数学动画引擎
- [FastAPI](https://github.com/tiangolo/fastapi) - 现代Web框架
- [OpenAI](https://openai.com/) - AI服务支持

---

<div align="center">
  <p>如果这个项目对你有帮助，请给我们一个 ⭐️</p>
  <p>Made with ❤️ by ClipTurbo Team</p>
</div>
