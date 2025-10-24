# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`dochain-block` is a Prefect Block distribution package that provides simple, focused authentication and connection blocks. Each service gets its own Block file following official Prefect patterns.

## Architecture Philosophy

### 🎯 Simple & Focused Design

**One Block Per File:**
- Each authentication service gets its own file
- Direct inheritance from `prefect.blocks.core.Block`
- No complex base classes or inheritance hierarchies

**Block vs Task Responsibility:**
- **Block**: Manages connection parameters, provides configured client
- **Task**: Uses Block client to perform business operations
- **Test**: Lightweight connectivity validation only

## Project Structure

```
dochain-block/
├── src/dochain_block/           # Main package directory
│   ├── __init__.py              # Package exports
│   ├── __version__.py           # Version information
│   └── nacos.py                # Nacos authentication Block (one class per file)
├── tests/                       # Test suite
│   ├── test_nacos.py            # Nacos Block tests
│   └── conftest.py             # pytest configuration and fixtures
├── examples/                    # Usage examples
│   └── nacos_example.py        # Nacos Block usage examples
├── .github/workflows/             # CI/CD pipeline
│   └── ci.yml                   # GitHub Actions workflow
└── pyproject.toml              # Package configuration
```

## Critical Development Rules

### ⚠️ DEPENDENCY MANAGEMENT: UV ONLY
- **NEVER** manually edit `pyproject.toml` to add dependencies
- **ALWAYS** use `uv add package-name` for production dependencies
- **ALWAYS** use `uv add --dev package-name` for development dependencies
- **ALWAYS** use `uv add --group group_name package-name` for optional dependency groups
- This ensures proper dependency resolution and environment management

### 🏗 Block Design Principles

**Simple Block Pattern:**
```python
# nacos.py
from prefect.blocks.core import Block
from pydantic import Field, HttpUrl, SecretStr
from nacos import NacosClient

class NacosBlock(Block):
    """Simple Nacos connection block."""

    _block_type_name = "Nacos Connection"
    _logo_url = "https://nacos.io/img/nacos-logo.png"

    server_url: HttpUrl = Field(..., description="Nacos server URL")
    namespace: str = Field(default="public")
    access_key: SecretStr | None = None
    secret_key: SecretStr | None = None

    def get_client(self) -> NacosClient:
        """Return configured Nacos client."""
        return NacosClient(
            server_addresses=str(self.server_url).rstrip('/'),
            namespace=self.namespace,
            ak=self.access_key.get_secret_value() if self.access_key else None,
            sk=self.secret_key.get_secret_value() if self.secret_key else None,
        )

    def test(self) -> str:
        """Lightweight connectivity test."""
        client = self.get_client()
        client.get_configs_list()  # Simple ping
        return "✅ Connected"
```

**Task Pattern (Business Operations):**
```python
# tasks.py
from prefect import task
from dochain_block import NacosBlock

@task
def get_nacos_config(data_id: str, group: str, block_name: str = "nacos-prod") -> str:
    """Get configuration from Nacos."""
    client = NacosBlock.load(block_name).get_client()
    return client.get_config(data_id, group)

@task
def publish_nacos_config(data_id: str, content: str, group: str, block_name: str) -> bool:
    """Publish configuration to Nacos."""
    client = NacosBlock.load(block_name).get_client()
    return client.publish_config(data_id, content, group)
```

**Usage in Flows:**
```python
from prefect import flow
from dochain_block import NacosBlock

@flow
def config_management_flow():
    # Block manages connection
    nacos_block = NacosBlock.load("my-nacos")

    # Test connection (Block method)
    print(nacos_block.test())

    # Business operations (Tasks)
    config = get_nacos_config.invoke("app.properties", "DEFAULT_GROUP")
    result = publish_nacos_config.invoke("new.properties", "value=true", "API_GROUP")

    return result
```

## Development Workflow

### 🔄 GitHub Actions CI/CD

**Automated Pipeline:**
```bash
# Push to main/master → Build package → Publish to PyPI
git push origin main

# Create release → Build → Publish to PyPI
# (Create release in GitHub UI)
```

**Pipeline Steps:**
1. **Build**: Create wheel distribution using `uv build`
2. **Publish**: Automatic PyPI release on GitHub release

### 🚀 PyPI Publishing

**Using Global PyPI Token (Recommended):**
```bash
# Configure once, all projects use it
gh auth login --with-token YOUR_PYPI_TOKEN

# Global tokens are automatically used by uv publish
uv publish --trusted-hosting pypi.org
```

**Release Workflow:**
1. Bump version in `pyproject.toml`
2. Create GitHub release with version tag
3. GitHub Actions automatically publishes to PyPI

### 🔧 Development Setup

**Environment Setup:**
```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # Unix/macOS
# or
.\.venv\Scripts\activate   # Windows

# Install in development mode
uv pip install -e ".[dev]"
```

**Dependency Management (IMPORTANT - UV ONLY):**
```bash
# Add dependencies - ALWAYS use uv add, NEVER edit pyproject.toml directly
uv add prefect                 # Core Prefect framework
uv add pydantic               # Data validation
uv add httpx                  # Async HTTP client
uv add --dev pytest           # Development dependency
uv add --dev pytest-asyncio    # Async testing support
uv add --dev pytest-cov         # Coverage reporting
uv add --dev hatchling          # Build tool

# Add optional dependencies with groups
uv add --group dev black ruff mypy  # Code quality tools

# Remove dependencies
uv remove package-name

# View current dependencies
uv pip list
```

## Common Development Tasks

### Adding New Authentication Blocks

**Create New Block File:**
```bash
# Create new authentication block
touch src/dochain_block/service_name.py
```

**Block Template:**
```python
from prefect.blocks.core import Block
from pydantic import Field, HttpUrl, SecretStr
from service_sdk import ServiceClient

class ServiceBlock(Block):
    """Service connection block."""

    _block_type_name = "Service Connection"
    _logo_url = "https://service.example.com/logo.png"

    server_url: HttpUrl = Field(..., description="Service server URL")
    token: SecretStr | None = None

    def get_client(self) -> ServiceClient:
        """Return configured Service client."""
        return ServiceClient(
            server_url=str(self.server_url),
            token=self.token.get_secret_value() if self.token else None,
        )

    def test(self) -> str:
        """Lightweight connectivity test."""
        client = self.get_client()
        client.ping()  # Simple connectivity check
        return "✅ Connected"
```

**Register in __init__.py:**
```python
from .service_name import ServiceBlock

__all__ = ["ServiceBlock", "__version__"]
```

**Create Tests:**
```bash
# Create test file
touch tests/test_service_name.py
```

## Key Implementation Notes

1. **Security First**: All sensitive data must use `SecretStr` type and never expose values in logs or repr
2. **Simple Blocks**: Each Block should only manage connection parameters and provide a client
3. **Async Tasks**: Business operations should be implemented as Prefect Tasks, not Block methods
4. **Testing**: Mock external services in tests to avoid dependency on real credentials
5. **Documentation**: Include comprehensive docstrings and type hints for all public APIs

## Prefect Integration

### Block Registration

Blocks are automatically registered when imported through package `__init__.py`.

### Block Saving/Loading

```bash
# Save block configuration
python -c "
from dochain_block import NacosBlock
block = NacosBlock(name='prod', server_url='https://nacos.example.com', username='user', password='pass')
block.save('nacos-prod')
"

# Load block in flows
from dochain_block import NacosBlock
block = NacosBlock.load('nacos-prod')
```

### Block Usage in Flows

```python
from prefect import flow

@flow
def my_flow():
    # Load saved block
    nacos = NacosBlock.load('my-nacos')

    # Get client for operations
    client = nacos.get_client()

    # Use client for business logic
    return client.get_config('app-config', 'DEFAULT_GROUP')
```

## Deployment Considerations

- **Simple Package**: Keep dependencies minimal and focused
- **Version Management**: Use semantic versioning in `pyproject.toml`
- **PyPI Publishing**: Automated through GitHub Actions on release
- **Testing**: Comprehensive test coverage with mocked services