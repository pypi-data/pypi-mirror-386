# Claude MPM Development Guidelines

This document provides development guidelines for the claude-mpm project codebase.

---

## 🔴 Critical Priority Index

**Essential items you MUST know immediately:**

1. **🔴 [Git Commit Format](#important-git-commit-message-format)** - Use Claude MPM branding, not Claude Code
2. **🔴 [Never Assume - Always Verify](#critical-principles)** - Core development principle
3. **🔴 [Quality Commands](#daily-development-commands)** - `make lint-fix`, `make quality`, `make safe-release-build`
4. **🔴 [File Organization](#project-structure-requirements)** - Scripts in `/scripts/`, tests in `/tests/`, modules in `/src/claude_mpm/`
5. **🔴 [Development Environment](#development-environment)** - Use `./scripts/claude-mpm` or activate venv directly
6. **🔴 [Temporary Files](#temporary-files-and-test-outputs)** - All temp files go in `/tmp/` directory

**🟡 Important items for effective development:**
- **[Architecture Overview](#architecture-v442)** - Service-oriented architecture with interfaces
- **[Documentation Index](#-primary-entry-point)** - Start here for navigation
- **[Service Development](#adding-a-new-service)** - Interface-based patterns
- **[Version Management](#version-management)** - Dual tracking system

**🟢 Recommended for comprehensive understanding:**
- **[Common Issues](#common-issues-and-solutions)** - Troubleshooting guide
- **[Contributing Guidelines](#contributing)** - Code quality standards
- **[Deployment Process](#deployment-process)** - Release procedures

---

## 🔴 IMPORTANT: Git Commit Message Format

When creating git commits in this project, ALWAYS use the Claude MPM branding:

```
Your commit message

🤖👥 Generated with [Claude MPM](https://github.com/bobmatnyc/claude-mpm)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**DO NOT USE**: `🤖 Generated with [Claude Code](https://claude.ai/code)`
**ALWAYS USE**: `🤖👥 Generated with [Claude MPM](https://github.com/bobmatnyc/claude-mpm)`

Note: A git hook at `.git/hooks/prepare-commit-msg` will automatically fix this if you forget.

## Project Overview

Claude MPM (Multi-Agent Project Manager) is a framework that extends Claude Code with orchestration capabilities for multiple specialized agents, featuring a modern service-oriented architecture with interface-based contracts and dependency injection.

## 🟡 Architecture (v4.4.2)

Following the TSK-0053 refactoring, Claude MPM features:

- **Service-Oriented Architecture**: Five specialized service domains
- **Interface-Based Contracts**: All services implement explicit interfaces  
- **Dependency Injection**: Service container with automatic resolution
- **Performance Optimizations**: Lazy loading, multi-level caching, connection pooling
- **Security Framework**: Input validation, path traversal prevention, secure operations
- **Backward Compatibility**: Lazy imports maintain existing import paths

## Key Documentation

### 📚 **Primary Entry Point**
- **[Documentation Index](docs/README.md)** - Start here! Complete navigation guide to all documentation

### Architecture and Development
- 🏗️ **Architecture Overview**: See [docs/developer/ARCHITECTURE.md](docs/developer/ARCHITECTURE.md) for service-oriented architecture
- 📁 **Project Structure**: See [docs/developer/STRUCTURE.md](docs/developer/STRUCTURE.md) for file organization
- 🔧 **Service Layer Guide**: See [docs/developer/SERVICES.md](docs/developer/SERVICES.md) for service development
- ⚡ **Performance Guide**: See [docs/developer/PERFORMANCE.md](docs/developer/PERFORMANCE.md) for optimization patterns
- 🔒 **Security Guide**: See [docs/reference/SECURITY.md](docs/reference/SECURITY.md) for security framework
- 🧪 **Testing Guide**: See [docs/developer/TESTING.md](docs/developer/TESTING.md) for testing strategies
- 📚 **Migration Guide**: See [docs/user/MIGRATION.md](docs/user/MIGRATION.md) for upgrade instructions

### Coding Agents (v4.9.0)
- 💻 **Coding Agents Catalog**: See [docs/reference/CODING_AGENTS.md](docs/reference/CODING_AGENTS.md) for 7 specialized coding agents
- 🎯 **Agent Capabilities**: See [docs/reference/AGENT_CAPABILITIES.md](docs/reference/AGENT_CAPABILITIES.md) for complete reference
- 🧪 **Agent Testing**: See [docs/developer/AGENT_TESTING.md](docs/developer/AGENT_TESTING.md) for 175-test infrastructure
- 📋 **Deployment Log**: See [docs/reference/AGENT_DEPLOYMENT_LOG.md](docs/reference/AGENT_DEPLOYMENT_LOG.md) for deployment history

### Operations and Quality
- 🧪 **Quality Assurance**: See [docs/developer/QA.md](docs/developer/QA.md) for testing guidelines
- 🚀 **Deployment**: See [docs/reference/DEPLOY.md](docs/reference/DEPLOY.md) for versioning and deployment
- 📊 **Response Logging**: See [docs/reference/RESPONSE_LOGGING_CONFIG.md](docs/reference/RESPONSE_LOGGING_CONFIG.md) for response logging configuration
- 🔢 **Versioning**: See [docs/reference/VERSIONING.md](docs/reference/VERSIONING.md) for version management
- 🧠 **Memory System**: See [docs/user/03-features/memory-system.md](docs/user/03-features/memory-system.md) for agent memory management
- 🎨 **Output Style**: See [docs/developer/OUTPUT_STYLE.md](docs/developer/OUTPUT_STYLE.md) for agent response formatting standards
- 📡 **Monitor & Dashboard**: See [docs/MONITOR.md](docs/MONITOR.md) for real-time event monitoring and visualization

## Development Guidelines

### Development Environment

Claude MPM uses Python virtual environments (venv) for dependency management:

- **Recommended**: Use `./scripts/claude-mpm` which automatically creates and activates the venv
- **Manual activation**: Run `source venv/bin/activate` (or `venv\Scripts\activate` on Windows)
- **Setup**: The venv is created automatically on first run with all required dependencies
- **Requirements**: Python 3.8+ required (see [DEVELOPMENT_SETUP.md](docs/user/getting-started/DEVELOPMENT_SETUP.md))

### 🔴 Critical Principles

**🔴 NEVER ASSUME - ALWAYS VERIFY**
- **NEVER assume** file locations, configurations, or implementations
- **ALWAYS verify** by reading actual files and checking current state
- **ALWAYS check** existing code patterns before implementing
- **NEVER guess** at directory structures or file contents
- **ALWAYS confirm** dependencies and imports exist before using them

### 🔴 Project Structure Requirements

**📋 Organization Standard**: See **[docs/reference/PROJECT_ORGANIZATION.md](docs/reference/PROJECT_ORGANIZATION.md)** for comprehensive organization rules and guidelines used by the `/mpm-organize` command.

1. **File Organization**: Always refer to `docs/developer/STRUCTURE.md` when creating new files
   - **Scripts**: ALL scripts go in `/scripts/`, NEVER in project root
   - **Tests**: ALL tests go in `/tests/`, NEVER in project root
   - **Python modules**: Always under `/src/claude_mpm/`
   - **Temporary files**: Always in `/tmp/`, NEVER committed to repo
   - **Documentation**: In `/docs/` by category (developer, user, reference, etc.)

2. **Import Conventions**:
   - Use full package names: `from claude_mpm.module import ...`
   - Never use relative imports in main code
   - Check existing patterns before adding new imports

3. **Organization Enforcement**:
   - Use `/mpm-organize --dry-run` to preview organization changes
   - Run `/mpm-organize` to apply organization standards
   - Structure validation runs automatically in pre-commit hooks

### 🔴 Testing Requirements

**Modern Quality Commands (Recommended):**
```bash
# Auto-fix formatting and import issues
make lint-fix

# Run all quality checks before commits
make quality

# Complete pre-release quality gate
make pre-publish
```

**Legacy Commands (Still Supported):**
```bash
# Quick E2E tests
./scripts/run_e2e_tests.sh

# Full test suite
./scripts/run_all_tests.sh

# Lint and type checks (catches duplicate imports!)
./scripts/run_lint.sh
```

See [docs/developer/QA.md](docs/developer/QA.md) for detailed testing procedures.
See [docs/developer/LINTING.md](docs/developer/LINTING.md) for linting configuration and duplicate import detection.

### Development Workflow

**Quality-First Development** - Use these three key commands for a smooth development experience:

#### Daily Development Commands

1. **`make lint-fix`** - Auto-fix formatting and import issues
   - Runs Black formatter, isort import sorting, and fixable Ruff issues
   - Use this frequently during development to maintain code quality
   - Safe to run anytime - only fixes issues, doesn't break code

2. **`make quality`** - Run all quality checks before commits
   - Comprehensive linting with Ruff, Black, isort, Flake8, mypy
   - Structure validation and code quality checks
   - **Run this before every commit** to catch issues early

3. **`make safe-release-build`** - Build with mandatory quality checks
   - Complete pre-publish quality gate plus build process
   - Ensures releases meet all quality standards
   - Required for all release builds

#### Quick Reference

| Command | When to Use | What It Does |
|---------|-------------|--------------|
| `make lint-fix` | During development | Auto-fixes formatting, imports, and simple issues |
| `make quality` | Before commits | Runs all quality checks and validations |
| `make safe-release-build` | For releases | Complete quality gate + safe build process |

For detailed quality gate documentation, see [docs/reference/DEPLOY.md#quality-gates](docs/reference/DEPLOY.md#quality-gates).

### Temporary Files and Test Outputs

**IMPORTANT**: All temporary test files, documentation drafts, and ephemeral outputs should be placed in the `/tmp/` directory:
- Test outputs and logs: `/tmp/test_results/`
- Documentation drafts: `/tmp/docs/`
- Debug outputs: `/tmp/debug/`
- Screenshot captures: `/tmp/screenshots/`
- Test scripts and experiments: `/tmp/scripts/`

The `/tmp/` directory is gitignored and will not be committed to the repository. This keeps the main codebase clean and prevents accidental commits of test artifacts.

**DO NOT** place test files or temporary documentation in:
- Project root directory
- `/scripts/` (reserved for production scripts)
- `/docs/` (reserved for final documentation)
- `/tests/` (reserved for permanent test suites)

### Key System Components

When modifying the codebase, understand these core systems:

1. **Framework Loader** (`src/claude_mpm/core/framework_loader.py`)
   - Loads PM instructions from `src/claude_mpm/agents/INSTRUCTIONS.md`
   - Manages agent discovery and capabilities
   - DO NOT duplicate CLAUDE.md content here

2. **Hook System** (`src/claude_mpm/hooks/`)
   - Extensibility through pre/post hooks
   - Response logging via `SubagentStop` and `Stop` events
   - Structured JSON responses for proper logging

3. **Services Layer** (`src/claude_mpm/services/`)
   - **Core Services**: Foundation interfaces and base classes
   - **Agent Services**: Agent lifecycle, deployment, and management
   - **Communication Services**: Real-time WebSocket and SocketIO
   - **Project Services**: Project analysis and workspace management
   - **Infrastructure Services**: Logging, monitoring, and error handling
   - **Legacy Structure**: Maintained for backward compatibility

4. **CLI System** (`src/claude_mpm/cli/`)
   - Modular command structure
   - See [CLI Architecture](src/claude_mpm/cli/README.md) for adding new commands

### Common Development Tasks

#### Adding a New Service
1. **Create Interface**: Define service contract in `src/claude_mpm/services/core/interfaces.py`
2. **Implement Service**: Create implementation in appropriate service domain
3. **Register Service**: Add to service container if using dependency injection
4. **Add Tests**: Create unit, integration, and interface compliance tests
5. **Update Documentation**: Document service in [docs/developer/SERVICES.md](docs/developer/SERVICES.md)

#### Service Development Patterns
```python
# 1. Define interface
class IMyService(ABC):
    @abstractmethod
    def my_operation(self, param: str) -> bool:
        pass

# 2. Implement service
class MyService(BaseService, IMyService):
    def __init__(self, dependency: IDependency):
        super().__init__("MyService")
        self.dependency = dependency
    
    async def initialize(self) -> bool:
        # Initialize service
        return True
    
    def my_operation(self, param: str) -> bool:
        # Implementation
        return True

# 3. Register in container
container.register(IMyService, MyService, singleton=True)

# 4. Test interface compliance
def test_service_implements_interface():
    service = MyService(mock_dependency)
    assert isinstance(service, IMyService)
```

#### Modifying PM Instructions
1. Edit `src/claude_mpm/agents/INSTRUCTIONS.md` for PM behavior
2. Edit `src/claude_mpm/agents/BASE_PM.md` for framework requirements
3. Test with `./claude-mpm run` in interactive mode
4. Update tests for PM behavior changes

#### Adding CLI Commands
1. Create command module in `src/claude_mpm/cli/commands/`
2. Register in `src/claude_mpm/cli/parser.py`
3. Follow existing command patterns
4. Use dependency injection for service access
5. Add comprehensive tests and documentation

#### Performance Optimization
1. **Identify Bottlenecks**: Use profiling tools and performance tests
2. **Implement Caching**: Add appropriate caching layers
3. **Lazy Loading**: Defer expensive operations until needed
4. **Connection Pooling**: Reuse expensive connections
5. **Monitor Metrics**: Track performance over time

## Common Issues and Solutions

### Architecture-Related Issues
1. **Service Resolution Errors**: Ensure services are registered in container before resolving
2. **Interface Compliance**: Verify services implement all required interface methods
3. **Circular Dependencies**: Use dependency injection and avoid circular imports
4. **Cache Performance**: Monitor cache hit rates and adjust TTL settings

### Legacy Compatibility Issues
1. **Import Errors**: Use new service paths or rely on lazy import compatibility
2. **Service Instantiation**: Use service container instead of direct instantiation
3. **Configuration Schema**: Update config files to new structure

### Performance Issues
1. **Slow Startup**: Check lazy loading implementation and cache warming
2. **Memory Usage**: Monitor service memory consumption and optimization
3. **Cache Misses**: Verify cache configuration and invalidation strategies

### Traditional Issues
1. **Import Errors**: Ensure virtual environment is activated and PYTHONPATH includes `src/`
2. **Hook Service Errors**: Check port availability (8765-8785)
3. **Version Errors**: Run `pip install -e .` to ensure proper installation
4. **Agent Deployment**: All agents now deploy to project-level `.claude/agents/` directory (changed in v4.0.32+)

## Contributing

### Code Quality Standards
1. **Follow Architecture**: Use service-oriented patterns and interface-based design
2. **Structure Compliance**: Follow the structure in `docs/developer/STRUCTURE.md`
3. **Interface Design**: Define clear contracts for all services
4. **Dependency Injection**: Use service container for loose coupling
5. **Performance**: Implement caching and lazy loading where appropriate
6. **Security**: Follow security guidelines in `docs/reference/SECURITY.md`

### Testing Requirements
1. **Unit Tests**: Test individual services and components (85%+ coverage)
2. **Integration Tests**: Test service interactions and interfaces
3. **Performance Tests**: Verify caching and optimization features
4. **Security Tests**: Validate input validation and security measures
5. **E2E Tests**: Test complete user workflows

### Documentation Standards
1. **Service Documentation**: Document all interfaces and implementations
2. **Architecture Updates**: Keep architecture docs current
3. **Migration Guides**: Document breaking changes and upgrade paths
4. **Performance Metrics**: Document performance expectations and benchmarks

### Version Management

Claude MPM uses a dual tracking system as of v4.0.25:
- **VERSION file**: Contains semantic version only (e.g., "3.9.5")
- **BUILD_NUMBER file**: Contains serial build number only (e.g., "275")
- **Combined display**: Three formats for different contexts:
  - Development: `3.9.5+build.275` (PEP 440 compliant)
  - UI/Logging: `v3.9.5-build.275` (user-friendly)
  - PyPI Release: `3.9.5` (clean semantic version)

Use [Conventional Commits](https://www.conventionalcommits.org/) for automatic versioning:
- `feat:` for new features (minor version bump)
- `fix:` for bug fixes (patch version bump)
- `feat!:` or `BREAKING CHANGE:` for breaking changes (major version bump)
- `perf:` for performance improvements
- `refactor:` for code refactoring
- `docs:` for documentation updates

Build numbers increment automatically with every substantial code change via git hooks.

## Deployment Process

See [docs/reference/DEPLOY.md](docs/reference/DEPLOY.md) for the complete deployment process:
- Version management with `./scripts/manage_version.py`
- Building and publishing to PyPI
- Creating GitHub releases
- Post-deployment verification

## Important Notes

- This file (CLAUDE.md) contains ONLY development guidelines for this project
- Framework features and usage are documented in the framework itself
- Claude Code automatically reads this file - keep it focused on development tasks
- Do not include end-user documentation or framework features here
- The refactored architecture enables faster development and better code quality
