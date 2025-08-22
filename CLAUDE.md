# CLAUDE.md
回复的时候要使用中文.
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Application Setup and Running
```bash
# Install dependencies
pip install -r requirements.txt

# Start the application
python main.py

# Start with debug mode (set debug: true in config.yaml first)
python main.py

# Run tests
pytest test_*.py

# Run with pytest-asyncio for async tests
pytest test_*.py -v

# Run specific test file
pytest test_modelscope_translation.py

# Run with coverage
pytest --cov=src test_*.py
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build
```

### Code Quality Tools
```bash
# Format code with black
black src/ main.py

# Lint with flake8
flake8 src/ main.py

# Type check with mypy
mypy src/ main.py

# Run all quality checks
black src/ main.py && flake8 src/ main.py && mypy src/ main.py
```

## High-Level Architecture

ClipTurbo is an AI-driven short video generation tool built on Python with a layered architecture:

### Core Architecture Layers

1. **Presentation Layer** - FastAPI web server providing RESTful APIs at `main.py:372`
2. **Business Logic Layer** - Core modules in `src/core/` managing projects and workflows
3. **AI Services Layer** - AI-powered services in `src/ai_services/` for content generation, translation, and TTS
4. **Rendering Engine Layer** - Manim-based video rendering in `src/manim_engine/`
5. **Data Layer** - SQLite/PostgreSQL for persistence with Redis for caching

### Key Components and Data Flow

**Main Entry Point**: `main.py` - FastAPI application that initializes and orchestrates all services. The app has three main operational modes:
- AI generation mode: Users provide a topic, AI generates complete content
- Direct content mode: Users provide structured content directly
- Template-based mode: Users select templates and customize parameters

**Core Services** (initialized in `main.py:85-133`):
- `AIOrchestrator` - Coordinates all AI services and manages processing workflows
- `TemplateManager` - Handles video template loading, validation, and parameter management
- `RenderManager` - Manages Manim rendering queue, concurrent jobs, and output quality
- `ProjectManager` - Handles project lifecycle, assets, and configuration
- `WorkflowEngine` - Orchestrates the entire video generation pipeline

**API Structure**:
- Project management: `/api/projects/*` - CRUD operations for video projects
- Template management: `/api/templates/*` - Template listing and parameter retrieval
- Video generation: `/api/generate` - Main endpoint for creating videos
- Workflow management: `/api/workflows/*` - Track generation progress and cancel jobs
- Render management: `/api/render/*` - Monitor rendering queue and job status

### Configuration System

The application uses a layered configuration approach:
- `config.yaml` - Main application configuration with service settings, database connections, and performance parameters
- `.env` file - Environment variables and API keys (copy from `.env.example`)
- Environment-specific overrides via environment variables with `${VAR_NAME}` syntax in YAML

Key configuration areas:
- AI services: TTS (EdgeTTS, Azure), translation, icon matching services
- Rendering: Quality presets, concurrent rendering limits, output directories
- Database: SQLite default, PostgreSQL optional
- Security: CORS settings, secret keys, file upload limits

### AI Services Integration

**AI Services** (`src/ai_services/`) are designed as pluggable components:
- `ContentGenerator` - Integrates with OpenAI GPT for script generation
- `TranslationService` - Supports multiple translation providers (ModelScope, Google, DeepL)
- `TTSService` - Multiple TTS providers with EdgeTTS as the free default
- `IconMatcher` - Image/icon matching from Unsplash, Pexels, or local libraries
- `AIOrchestrator` - Central coordinator that manages service dependencies and caching

### Manim Rendering Engine

**Rendering Pipeline** (`src/manim_engine/`) is built on Manim:
- `TemplateManager` - Loads and validates video templates with parameter schemas
- `RenderManager` - Queue-based rendering system with quality presets and concurrency control
- `AssetManager` - Handles fonts, images, audio processing and caching
- Template system supports both built-in templates and custom user-defined templates

### Development Patterns

When working with this codebase:
1. **Service Initialization**: All services are initialized in `main.py:startup_event()` with proper error handling
2. **Async Operations**: Heavy operations (rendering, AI processing) use async patterns with proper error handling
3. **Configuration Management**: Use the config system with environment variable substitution
4. **Logging**: Comprehensive logging is set up with file and console outputs
5. **Testing**: Use pytest for testing, with separate test files for specific services
6. **Docker Development**: The application is containerized with health checks and proper volume mounts

### File Structure Conventions

- `src/` - Core application modules organized by domain
- `examples/` - Usage examples and sample implementations
- `output/` - Generated videos and artifacts
- `projects/` - Project data and configurations
- `uploads/` - User-uploaded assets
- `temp/` - Temporary files during processing
- `logs/` - Application logs with rotation

### Environment Requirements

- Python 3.9+ (3.11 recommended)
- FFmpeg for video processing
- Redis (optional, for caching and task queue)
- PostgreSQL (optional, defaults to SQLite)
- System dependencies for Manim (Cairo, Pango, etc.)