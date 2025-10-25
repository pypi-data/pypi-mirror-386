<img src="https://raw.githubusercontent.com/dialectus-ai/dialectus-engine/main/assets/logo.png" alt="Dialectus Engine" width="350">

<br />

# Dialectus Engine

A Python library for orchestrating AI-powered debates with multi-provider model support.

![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen.svg)

> **Ready-to-Use CLI:** Want to run debates right away? Check out the [dialectus-cli](https://github.com/dialectus-ai/dialectus-cli) - a command-line interface that uses this engine to run debates locally with a beautiful terminal UI.

## Overview

The Dialectus Engine is a standalone Python library that provides core debate orchestration logic, including participant coordination, turn management, AI judge integration, and multi-provider model support. It's designed to be imported and used by other applications to build debate systems.

## Components

- **Core Engine** (`debate_engine/`) - Main debate orchestration logic
- **Models** (`models/`) - AI model provider integrations (Ollama, OpenRouter, Anthropic)
- **Configuration** (`config/`) - System configuration management
- **Judges** (`judges/`) - AI judge implementations with ensemble support
- **Formats** (`formats/`) - Debate format definitions (Oxford, Parliamentary, Socratic, Public Forum)
- **Moderation** (`moderation/`) - Optional content safety system for debate topics

## Installation

### From PyPI

**Using uv (recommended):**
```bash
uv pip install dialectus-engine
```

**Using pip:**
```bash
pip install dialectus-engine
```

### From Source

**Using uv (recommended, faster):**
```bash
# Clone the repository
git clone https://github.com/dialectus-ai/dialectus-engine.git
cd dialectus-engine

# Install in development mode with all dev dependencies
uv sync

# Or install without dev dependencies
uv pip install -e .
```

**Using pip:**
```bash
# Clone the repository
git clone https://github.com/dialectus-ai/dialectus-engine.git
cd dialectus-engine

# Install in development mode
pip install -e .

# Or install with dev dependencies
pip install -e ".[dev]"
```

### As a Dependency

Add to your `pyproject.toml`:

```toml
[project]
dependencies = [
    "dialectus-engine>=0.1.0",
]
```

Or install directly from git:

```bash
# Using uv
uv pip install git+https://github.com/dialectus-ai/dialectus-engine.git@main

# Using pip
pip install git+https://github.com/dialectus-ai/dialectus-engine.git@main
```

## Quick Start

```python
import asyncio
from pathlib import Path
from dialectus.engine.debate_engine import DebateEngine
from dialectus.engine.models.manager import ModelManager
from dialectus.engine.config.settings import AppConfig

async def run_debate():
    # Load configuration
    config = AppConfig.load_from_file(Path("debate_config.json"))

    # Create model manager from config
    model_manager = ModelManager.from_config(config)

    # Create debate engine
    engine = DebateEngine(config=config, model_manager=model_manager)

    # Run debate
    transcript = await engine.run_debate()
    print(transcript)

asyncio.run(run_debate())
```

## Configuration

The engine uses `debate_config.json` for system configuration. To get started:

```bash
# Linux/Mac: Copy the example configuration
cp debate_config.example.json debate_config.json

# Windows (PowerShell):
# copy debate_config.example.json debate_config.json

# Edit with your settings and API keys
# Linux/Mac: nano debate_config.json
# Windows: notepad debate_config.json
# Or use your preferred editor (VS Code, vim, etc.)
```

Key configuration sections:
- **Models**: Define debate participants with provider, personality, and parameters
- **Providers**: Configure Ollama (local), OpenRouter (cloud), and Anthropic (cloud) settings
- **Judging**: Set evaluation criteria and judge models
- **Debate**: Default topic, format, and word limits
- **Moderation** (optional): Content safety for user-provided topics

For detailed configuration documentation, see [CONFIG_GUIDE.md](CONFIG_GUIDE.md).

## Development Workflows

### Running Tests and Type Checking

**Using uv (recommended):**
```bash
# Run tests
uv run pytest

# Type check with Pyright
uv run pyright

# Lint with ruff
uv run ruff check .

# Format with ruff
uv run ruff format .
```

**Using pip:**
```bash
# Ensure dev dependencies are installed
pip install -e ".[dev]"

# Run tests
pytest

# Type check with Pyright
pyright

# Lint and format
ruff check .
ruff format .
```

### Building Distribution

**Using uv:**
```bash
# Build wheel and sdist
uv build

# Install locally from wheel
uv pip install dist/dialectus_engine-*.whl
```

**Using pip:**
```bash
# Build wheel and sdist
python -m build

# Install locally
pip install dist/dialectus_engine-*.whl
```

### Managing Dependencies

**Using uv:**
```bash
# Add a new dependency
# 1. Edit pyproject.toml [project.dependencies] section
# 2. Update lock file and sync environment:
uv lock && uv sync

# Upgrade all dependencies (within version constraints)
uv lock --upgrade

# Upgrade specific package
uv lock --upgrade-package httpx

# Add dev dependency
# 1. Edit pyproject.toml [project.optional-dependencies.dev]
# 2. Run:
uv sync
```

**Using pip:**
```bash
# Add a new dependency
# 1. Edit pyproject.toml dependencies
# 2. Reinstall:
pip install -e ".[dev]"
```

### Why uv?

- **10-100x faster** than pip for installs and resolution
- **Reproducible builds** via `uv.lock` (cross-platform, includes hashes)
- **Python 3.14 ready** - Takes advantage of free-threading for even better performance
- **Single source of truth** - Dependencies in `pyproject.toml`, lock file auto-generated
- **Compatible** - `pip` still works perfectly with `pyproject.toml`

## Features

### Multi-Provider Model Support
- **Ollama**: Local model management with hardware optimization
- **OpenRouter**: Cloud model access to a wide variety of models
- **Anthropic**: Direct access to Claude models
- **Async streaming**: Chunk-by-chunk response generation for all providers
- **Auto-discovery**: Dynamic model listing from all configured providers
- **Caching**: In-memory cache with TTL for model metadata
- **Cost tracking**: Token usage and cost calculation for cloud providers

### Debate Formats
- **Oxford**: Classic opening/rebuttal/closing structure
- **Parliamentary**: British-style government vs. opposition
- **Socratic**: Question-driven dialogue format
- **Public Forum**: American high school debate style

### AI Judge System
- **LLM-based evaluation**: Detailed criterion scoring
- **Ensemble judging**: Aggregate decisions from multiple judges
- **Structured decisions**: JSON-serializable judge results
- **Configurable criteria**: Logic, evidence, persuasiveness, etc.

### Content Moderation (Optional)
- **Multi-provider support**: Ollama (local), OpenRouter, OpenAI moderation API
- **Safety categories**: Harassment, hate speech, violence, sexual content, dangerous activities
- **Flexible deployment**: Enable for production APIs, disable for trusted environments
- **Graceful error handling**: Provider-specific rate limit handling and retry logic

## Architecture

Key architectural principles:
- **Library-first**: Designed to be imported by other applications
- **Provider agnostic**: Support for multiple AI model sources
- **Async by default**: All model interactions are async
- **Type-safe**: Strict Pyright configuration with modern type hints
- **Pydantic everywhere**: All config and data models use Pydantic v2
- **Configurable**: JSON-based configuration with validation

### Technology Stack
- **Python 3.13+** with modern type hints (`X | None`, `list[T]`, `dict[K, V]`)
- **Pydantic v2** for data validation and settings management
- **OpenAI SDK** for OpenRouter API integration (streaming support)
- **httpx** for async HTTP requests (Ollama provider)
- **asyncio** for concurrent debate operations

## Usage Examples

### Listing Available Models

```python
from models.manager import ModelManager

async def list_models():
    manager = ModelManager()
    models = await manager.get_all_models()
    for model_id, model_info in models.items():
        print(f"{model_id}: {model_info.description}")
```

### Running a Custom Format

```python
from formats.registry import format_registry

# Get available formats
formats = format_registry.list_formats()

# Load a specific format
oxford = format_registry.get_format("oxford")
phases = oxford.phases()
```

### Ensemble Judging

```python
from judges.factory import JudgeFactory

# Create judge with multiple models
config.judging.judge_models = ["openthinker:7b", "llama3.2:3b", "qwen2.5:3b"]
judge = JudgeFactory.create_judge(config.judging, model_manager)

# Get aggregated decision
decision = await judge.judge_debate(context)
```

### Content Moderation

```python
from dialectus.engine.moderation import ModerationManager, TopicRejectedError

# Create moderation manager
manager = ModerationManager(config.moderation, config.system)

# Validate user-provided topic
user_topic = "Should AI be regulated?"

try:
    result = await manager.moderate_topic(user_topic)
    # Topic is safe, proceed with debate
    print(f"Topic approved with confidence: {result.confidence}")
except TopicRejectedError as e:
    # Topic violates content policy
    print(f"Topic rejected: {e.reason}")
    print(f"Violated categories: {', '.join(e.categories)}")
```

For comprehensive moderation testing and setup instructions, see [MODERATION_TESTING.md](MODERATION_TESTING.md).

## Provider Setup

### Anthropic (Claude Models)

To use Anthropic's Claude models, you'll need an API key:

1. **Get an API key**: Sign up at [console.anthropic.com](https://console.anthropic.com/)

2. **Set your API key** (choose one method):

   **Environment variable (recommended):**
   ```bash
   export ANTHROPIC_API_KEY="sk-ant-api03-..."
   ```

   **Or in `debate_config.json`:**
   ```json
   {
     "system": {
       "anthropic": {
         "api_key": "sk-ant-api03-...",
         "base_url": "https://api.anthropic.com/v1",
         "max_retries": 3,
         "timeout": 60
       }
     }
   }
   ```

3. **Configure a model**:
   ```json
   {
     "models": {
       "model_a": {
         "name": "claude-3-5-sonnet-20241022",
         "provider": "anthropic",
         "personality": "analytical",
         "max_tokens": 300,
         "temperature": 0.7
       }
     }
   }
   ```

**Finding available models:**

Anthropic provides a `/v1/models` API endpoint to list available models. You can also check [Anthropic's model documentation](https://docs.anthropic.com/en/docs/models-overview) for the latest models and their capabilities.

### OpenRouter

To use OpenRouter's model marketplace:

1. **Get an API key**: Sign up at [openrouter.ai](https://openrouter.ai/)

2. **Set your API key**:
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   ```

3. **Configure a model**:
   ```json
   {
     "models": {
       "model_a": {
         "name": "anthropic/claude-3.5-sonnet",
         "provider": "openrouter",
         "personality": "analytical",
         "max_tokens": 300,
         "temperature": 0.7
       }
     }
   }
   ```

### Ollama (Local Models)

To use local models via Ollama:

1. **Install Ollama**: Download from [ollama.com](https://ollama.com/)

2. **Pull models**:
   ```bash
   ollama pull llama3.2:3b
   ollama pull qwen2.5:7b
   ```

3. **Configure**:
   ```json
   {
     "models": {
       "model_a": {
         "name": "llama3.2:3b",
         "provider": "ollama",
         "personality": "analytical",
         "max_tokens": 300,
         "temperature": 0.7
       }
     },
     "system": {
       "ollama_base_url": "http://localhost:11434"
     }
   }
   ```
