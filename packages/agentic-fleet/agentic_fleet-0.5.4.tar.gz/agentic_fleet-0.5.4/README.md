# AgenticFleet

![AgenticFleet Architecture](docs/banner.png)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![PyPI Downloads](https://static.pepy.tech/personalized-badge/agentic-fleet?period=total&units=INTERNATIONAL_SYSTEM&left_color=GREY&right_color=BLUE&left_text=downloads)](https://pepy.tech/projects/agentic-fleet)

> **⚠️ Active Development Notice**
> This project is under active development. Features, APIs, and workflows may change. We recommend pinning to specific versions for production use.

---

## AgenticFleet Overview

- 🖥️ **Interactive CLI** – Rich terminal interface for direct agent interaction
- 🌐 **Web Frontend** – Modern React UI wired to agent-as-workflow pattern (default)
- 📓 **Jupyter Notebooks** – Exploration and prototyping environments in `notebooks/`

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** package manager
- **OpenAI API key** (set as `OPENAI_API_KEY`)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Qredence/agentic-fleet.git
cd agentic-fleet

# 2. Configure environment
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY

# 3. Install dependencies
make install

# 4. Launch the fleet (runs frontend + backend)
uv run agentic-fleet
# Alternatives:
#   make dev          # Same as agentic-fleet
#   uv run fleet      # CLI/REPL only
```

## ✨ Key Features

- **🎯 Magentic-Native Architecture** – Built on Microsoft Agent Framework's `MagenticBuilder` with intelligent planning and progress evaluation
- **🤖 Specialized Agent Fleet** – Pre-configured researcher, coder, and analyst agents with domain-specific tools
- **🌐 Modern Web Frontend** – React-based UI with agent-as-workflow pattern for seamless agent interaction
- **📓 Interactive Notebooks** – Jupyter notebooks for experimentation, prototyping, and learning
- **💾 State Persistence** – Checkpoint system saves 50-80% on retry costs by avoiding redundant LLM calls
- **🛡️ Human-in-the-Loop (HITL)** – Configurable approval gates for code execution, file operations, and sensitive actions
- **📊 Full Observability** – Event-driven callbacks for streaming responses, plan tracking, and tool monitoring
- **🧠 Long-term Memory** – Optional Mem0 integration with Azure AI Search for persistent context
- **🔧 Declarative Configuration** – YAML-based agent configuration for non-engineers to tune prompts and tools
- **🎨 Multiple Interfaces** – CLI, web frontend, and notebooks for different workflows

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** package manager
- **OpenAI API key** (set as `OPENAI_API_KEY`)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Qredence/agentic-fleet.git
cd agentic-fleet

# 2. Configure environment
cp .env.example .env
# Edit .env to add your OPENAI_API_KEY

# 3. Install dependencies
make install

# 4. Launch the fleet (runs frontend + backend)
uv run agentic-fleet
# Frontend runs on port 5173, backend on port 8000
# Alternatives:
#   make dev          # Same as agentic-fleet
#   uv run fleet      # CLI/REPL only
```

### First Run

**Web Frontend (Default):**
Run `uv run agentic-fleet` (or `make dev`) to launch both frontend and backend. Access the web UI at `http://localhost:5173` to interact with agents through a modern React interface using the agent-as-workflow pattern.

**CLI Interface:**
For command-line interaction only, run `uv run fleet`:

```text
AgenticFleet v0.5.4
________________________________________________________________________
Task                ➤ Analyze Python code quality in my repository
Plan · Iteration 1  Facts: User needs code analysis | Plan: Use coder agent...
Progress            Status: In progress | Next speaker: coder
Agent · coder       Analyzing repository structure...
Result              Found 12 files, 3 quality issues...
```

**Built-in CLI commands:**

- History navigation: `↑` / `↓` or `Ctrl+R`
- Checkpoints: `checkpoints`, `resume <id>`
- Exit: `quit` or `Ctrl+D`

**Jupyter Notebooks:**
Explore example workflows in `notebooks/` including:

- `magentic.ipynb` – Magentic One pattern examples
- `agent_as_workflow.ipynb` – Agent-as-workflow demonstrations
- `mem0_basic.ipynb` – Memory integration tutorial
- `azure_responses_client.ipynb` – Azure AI responses client usage

---

## 🎯 Current Status

**✅ Production Ready - v0.5.4**

AgenticFleet is now **production-ready** with enterprise-grade features:

- **🔒 Type Safe**: 100% mypy compliance, zero type errors
- **🧪 Well Tested**: Configuration validation + orchestration tests
- **📊 Observable**: Full OpenTelemetry tracing integrated
- **🛡️ Secure**: Human-in-the-loop approval system
- **⚡ Performant**: Checkpoint system reduces retry costs by 50-80%
- **🎨 Modern UI**: Production-ready React frontend with real-time streaming

---

## 🏗️ Architecture

AgenticFleet implements the **Magentic One** workflow pattern with a manager-executor architecture:

### Workflow Cycle

1. **PLAN** – Manager analyzes task, gathers facts, creates structured action plan
2. **EVALUATE** – Progress ledger checks: request satisfied? in a loop? who acts next?
3. **ACT** – Selected specialist executes with domain-specific tools, returns findings
4. **OBSERVE** – Manager reviews response, updates context, decides next action
5. **REPEAT** – Continues until completion or limits reached (configurable in `workflow.yaml`)

### Agent Specialists

| Agent            | Model Default | Tools                                                 | Purpose                           |
| ---------------- | ------------- | ----------------------------------------------------- | --------------------------------- |
| **Orchestrator** | `gpt-5`       | (none)                                                | Task planning & result synthesis  |
| **Researcher**   | `gpt-5`       | `web_search_tool`                                     | Information gathering & citations |
| **Coder**        | `gpt-5-codex` | `code_interpreter_tool` (Microsoft hosted sandbox)    | Code generation & analysis        |
| **Analyst**      | `gpt-5`       | `data_analysis_tool`, `visualization_suggestion_tool` | Data exploration & insights       |

All agents use **OpenAI Response API** format via `OpenAIResponsesClient` and return structured Pydantic models for reliable downstream parsing.

See **[Architecture Documentation](docs/architecture/magentic-fleet.md)** for detailed design patterns.

---

## ⚙️ Configuration

AgenticFleet uses a **declarative YAML-first** approach:

### Workflow Configuration (`config/workflow.yaml`)

```yaml
fleet:
  manager:
    model: "gpt-5"
    instructions: |
      You coordinate researcher, coder, and analyst agents.
      Delegate based on task requirements...

  orchestrator:
    max_round_count: 30 # Maximum workflow iterations
    max_stall_count: 3 # Triggers replan
    max_reset_count: 2 # Complete restart limit

  callbacks:
    streaming_enabled: true
    log_progress_ledger: true
```

### Per-Agent Configuration (`agents/<role>/config.yaml`)

```yaml
name: researcher
model: gpt-5
temperature: 0.3
max_tokens: 4000

system_prompt: |
  You are a research specialist. Use web_search_tool to find information...

tools:
  - name: web_search_tool
    enabled: true
```

### Environment Variables (`.env`)

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional: Memory (Mem0)
MEM0_HISTORY_DB_PATH=./var/mem0
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Optional: Observability
ENABLE_OTEL=true
OTLP_ENDPOINT=http://localhost:4317
```

---

## 🛠️ Development

### Setup Development Environment

```bash
# Install with dev dependencies
make install

# Run configuration validation
make test-config

# Run all quality checks (lint, format, type-check)
make check

# Run test suite
make test
```

### Development Commands

All commands use `uv run` prefix (managed by Makefile):

| Command                | Purpose                                 |
| ---------------------- | --------------------------------------- |
| `uv run agentic-fleet` | Launch frontend + backend (full stack)  |
| `uv run fleet`         | CLI/REPL interface only                 |
| `make dev`             | Same as agentic-fleet                   |
| `make test`            | Run full test suite                     |
| `make test-config`     | Validate YAML configs & agent factories |
| `make lint`            | Check code with Ruff                    |
| `make format`          | Auto-format with Black + Ruff           |
| `make type-check`      | Run mypy strict type checking           |
| `make check`           | Chain lint + format + type checks       |

### Testing Patterns

- **Configuration Tests**: `tests/test_config.py` validates env vars, YAML structure, tool imports
- **Fleet Tests**: `tests/test_magentic_fleet.py` covers 14 orchestration scenarios
- **Memory Tests**: `tests/test_mem0_context_provider.py` validates Mem0 integration
- **Mock LLM Calls**: Always patch `OpenAIResponsesClient` to avoid API costs in tests

### Code Quality Standards

- **Python 3.12+** with strict typing (`Type | None` instead of `Optional[Type]`)
- **100-character line limit** (Black formatter)
- **Ruff linting** with `pyupgrade` and `isort` rules
- **MyPy strict checks** (except for test files)
- **Pydantic models** for all tool return types

See **[Contributing Guide](docs/project/CONTRIBUTING.md)** for detailed conventions.

---

## 📖 Documentation

Comprehensive documentation organized by audience:

### For Users

- **[Getting Started](docs/getting-started/)** – Installation, configuration, first steps
- **[User Guides](docs/guides/)** – Task-oriented tutorials
- **[Agent Catalog](docs/project/AGENTS.md)** – Detailed agent capabilities & tools
- **[Troubleshooting](docs/troubleshooting/)** – FAQ & common issues

### For Developers

- **[Architecture](docs/architecture/)** – System design & patterns
- **[Features](docs/features/)** – Implementation deep-dives
- **[Contributing](docs/project/CONTRIBUTING.md)** – Development workflow & standards
- **[API Reference](docs/api/)** – REST API & Python SDK

**[📚 Documentation Index](docs/README.md)** – Complete navigation guide

---

## 🆕 Release Notes

### v0.5.4 (2025-10-23)

- **Memory Bank Integration**: Added comprehensive memory-bank instructions for AI context persistence
- **Documentation Expansion**: Enhanced AGENTS documentation with detailed capability descriptions
- **UI/UX Polish**: Significant frontend improvements for better user experience
- **Backend Cleanup**: Code quality improvements and architectural refinements
- **Security Enhancements**: Fixed workflow permissions and expression injection vulnerabilities
- **CI/CD Improvements**: Updated workflows for release triggering and code scanning
- **Version Management**: Consistent v0.5.4 versioning across all documentation

---

## 🔧 Adding Custom Agents

Extend the fleet with domain-specific agents:

### 1. Scaffold Agent Structure

```bash
mkdir -p src/agenticfleet/agents/planner/{tools,}
touch src/agenticfleet/agents/planner/{__init__.py,agent.py,config.yaml}
```

### 2. Create Agent Factory

```python
# src/agenticfleet/agents/planner/agent.py
from agenticfleet.config.settings import settings
from agent_framework import ChatAgent
from agent_framework.azure_ai import OpenAIResponsesClient

def create_planner_agent() -> ChatAgent:
    config = settings.load_agent_config("planner")

    return ChatAgent(
        name=config["name"],
        model=config["model"],
        system_prompt=config["system_prompt"],
        client=OpenAIResponsesClient(model_id=config["model"]),
        tools=[],  # Add tools here
    )
```

#

## 🤝 Contributing

We welcome contributions! Please follow these steps:

### Before You Start

1. Read **[Contributing Guidelines](docs/project/CONTRIBUTING.md)**
2. Review **[Code of Conduct](CODE_OF_CONDUCT.md)**
3. Check existing **[Issues](https://github.com/Qredence/agentic-fleet/issues)**

### Development Process

```bash
# 1. Fork & clone
git clone https://github.com/YOUR_USERNAME/agentic-fleet.git
cd agentic-fleet

# 2. Create feature branch
git checkout -b feat/your-feature

# 3. Make changes
# Edit code, update docs, add tests

# 4. Run quality checks
make check          # Lint, format, type-check
make test-config    # Validate configurations
make test           # Full test suite

# 5. Commit with conventional format
git commit -m "feat(agents): add planner agent with breakdown tool"

# 6. Push & open PR
git push origin feat/your-feature
```

### Pull Request Checklist

- ✅ Tests pass (`make test`)
- ✅ Code formatted (`make check`)
- ✅ Documentation updated
- ✅ YAML configs validated (`make test-config`)
- ✅ Commit messages follow `feat:`, `fix:`, `docs:` convention

---

## 🔐 Security

### Reporting Vulnerabilities

**Do NOT open public issues for security vulnerabilities.**

Please follow the process outlined in **[SECURITY.md](docs/project/SECURITY.md)**.

### Security Best Practices

- Store API keys in `.env` (never commit)
- Use HITL approval for code execution
- Enable audit logging for sensitive operations
- Review tool permissions in agent configs
- Keep dependencies updated (`uv sync`)

---

## 📄 License

AgenticFleet is released under the **[MIT License](LICENSE)**.

```
Copyright (c) 2025 Qredence

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

See **[LICENSE](LICENSE)** for full terms.

---

## 🙏 Acknowledgments

Built with:

- **[Microsoft Agent Framework](https://github.com/microsoft/agent-framework)** – Core orchestration
- **[Mem0](https://mem0.ai/)** – Long-term memory layer
- **[uv](https://docs.astral.sh/uv/)** – Fast Python package manager
- **[Rich](https://rich.readthedocs.io/)** – Beautiful terminal UI
- **[Pydantic](https://docs.pydantic.dev/)** – Data validation

Special thanks to the Microsoft Agent Framework team for the Magentic One pattern.

---

## 📞 Support & Community

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/Qredence/agentic-fleet/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Qredence/agentic-fleet/discussions)
- **Website**: [qredence.ai](https://qredence.ai)

---

**[⬆ Back to Top](#agenticfleet)**

Made with ❤️ by [Qredence](https://github.com/Qredence)
