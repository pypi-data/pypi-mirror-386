# Building Pydantic Config Classes with Multi-Pattern Support

This document provides a comprehensive guide for implementing Pydantic configuration classes that support three initialization patterns: Direct Python Configuration, Environment Variables, and .env File Configuration.

## Overview

The Context Bridge configuration system demonstrates how to build flexible, type-safe configuration management that supports:

1. **Direct Python Configuration** - Recommended for PyPI package users
2. **Environment Variables** - Recommended for Docker/Kubernetes deployments
3. **.env File Configuration** - Convenient for local development

## Core Implementation

### 1. Base Configuration Class

```python
"""Configuration settings for Your Package.

Supports three configuration methods:
1. Direct Python instantiation (recommended for PyPI installs)
2. Environment variables (recommended for Docker/Kubernetes)
3. .env file (convenient for local development only)

The .env file loading is optional and only attempted if python-dotenv is available.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator

# Optional .env loading - only if python-dotenv is available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, just use environment variables
    pass


class Config(BaseModel):
    """Configuration for Your Package.

    This class provides type-safe configuration management and supports three
    initialization patterns:

    **Pattern 1: Direct Python (Recommended for PyPI users)**
    ```python
    from your_package import YourClass, Config

    config = Config(
        database_host="localhost",
        database_password="secure_password",
        api_key="your_api_key"
    )

    instance = YourClass(config=config)
    ```

    **Pattern 2: Environment Variables (Recommended for Docker/K8s)**
    ```bash
    export DATABASE_HOST=postgres
    export DATABASE_PASSWORD=secure_pass
    export API_KEY=your_key
    python your_app.py
    ```
    ```python
    from your_package import YourClass

    instance = YourClass()  # Uses environment variables
    ```

    **Pattern 3: .env File (Convenient for local development)**
    ```bash
    # .env (git-ignored)
    DATABASE_HOST=localhost
    DATABASE_PASSWORD=devpass
    API_KEY=dev_key
    ```
    ```python
    # Automatically loaded if python-dotenv is available
    from your_package import YourClass

    instance = YourClass()  # Uses .env file
    ```
    """

    # Configuration Fields
    # Use Field with default_factory to read from environment variables
    database_host: str = Field(default_factory=lambda: os.getenv("DATABASE_HOST", "localhost"))
    database_port: int = Field(default_factory=lambda: int(os.getenv("DATABASE_PORT", "5432")))
    database_user: str = Field(default_factory=lambda: os.getenv("DATABASE_USER", "postgres"))
    database_password: str = Field(default_factory=lambda: os.getenv("DATABASE_PASSWORD", ""))
    database_name: str = Field(default_factory=lambda: os.getenv("DATABASE_NAME", "your_db"))

    # API Configuration
    api_key: str = Field(default_factory=lambda: os.getenv("API_KEY", ""))
    api_base_url: str = Field(default_factory=lambda: os.getenv("API_BASE_URL", "https://api.example.com"))

    # Application Settings
    debug_mode: bool = Field(default_factory=lambda: os.getenv("DEBUG_MODE", "false").lower() == "true")
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    # Pydantic Configuration
    model_config = ConfigDict(
        env_file=".env",  # Optional .env loading - only loaded if file exists
        env_file_encoding="utf-8",
        case_sensitive=False,  # Treat env var names case-insensitively
        extra="ignore",  # Ignore extra fields not defined in Config model
    )

    @field_validator("database_password")
    @classmethod
    def validate_password(cls, v: str, info) -> str:
        """Validate that passwords meet minimum security requirements.

        Only validates if a password is actually provided (non-empty).
        This allows development with default empty password while requiring
        secure passwords in production configs.
        """
        if v and len(v) < 8:
            raise ValueError(
                f"{info.field_name} must be at least 8 characters long for security. "
                f"Current length: {len(v)}"
            )
        return v

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str, info) -> str:
        """Validate API key format if provided."""
        if v and not v.startswith(("sk-", "pk_", "Bearer ")):
            # Add your API key validation logic here
            pass
        return v
```

### 2. Global Config Functions (Optional)

```python
# Global config instance (for backward compatibility)
# This is optional - the recommended pattern is to pass Config directly
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance.

    **Use Case**: Fallback pattern for CLI scripts, services, and tests.
    This maintains a global singleton for convenience when a Config can't be
    passed directly through the call stack.

    **Recommended for:**
    - CLI tools
    - Service classes that accept optional config parameter
    - Test scripts that need quick config access

    **NOT Recommended for:**
    - Main application code - pass Config explicitly instead
    - Library code - accept Config as parameter

    The returned Config is loaded in this order (first match wins):
    1. Environment variables (DATABASE_HOST, etc.)
    2. .env file (if python-dotenv is available and file exists)
    3. Default hardcoded values

    Example:
        ```python
        # For CLI scripts - OK to use get_config()
        from your_package.config import get_config
        config = get_config()
        manager = DatabaseManager(config)

        # For main app - pass Config explicitly (BETTER)
        from your_package import YourClass, Config
        config = Config(database_host="localhost", ...)
        instance = YourClass(config=config)
        ```

    Returns:
        Config object loaded from environment variables, .env file, or defaults
    """
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance.

    **Use Case**: Mainly for testing or CLI scripts that need to override config.

    Use this to temporarily set a different config for:
    - Unit tests (mock configurations)
    - Testing different database connections
    - CLI tools that load config dynamically

    **NOT Recommended for:**
    - Production code - pass Config to your classes instead
    - Library code - accept Config as parameter

    Example:
        ```python
        # For testing - OK to use set_config()
        test_config = Config(database_name="test_db", ...)
        set_config(test_config)
        config = get_config()  # Returns test_config

        # For production - pass Config directly (BETTER)
        config = Config(...)
        instance = YourClass(config=config)
        ```

    Args:
        config: Configuration object to set as global instance
    """
    global _config
    _config = config
```

### 3. Core Class Integration

```python
from typing import Optional
from .config import Config, get_config


class YourCoreClass:
    """Your main package class that uses the configuration."""

    def __init__(self, config: Optional[Config] = None):
        """
        Initialize YourCoreClass.

        Args:
            config: Optional Config object. If not provided, creates a new Config
                   that loads from environment variables and .env file (if available).

        Example:
            ```python
            # With explicit config
            config = Config(database_host="localhost", ...)
            instance = YourCoreClass(config=config)

            # With environment variables / .env
            instance = YourCoreClass()
            ```
        """
        self.config = config or Config()

    def get_config(self) -> Config:
        """Get the current configuration."""
        return self.config
```

## Dependency Management

### pyproject.toml Configuration

```toml
[project]
name = "your-package"
version = "0.1.0"
dependencies = [
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    # ... other core dependencies
]

[project.optional-dependencies]
dev = [
    "python-dotenv>=1.0.0",  # Only for local development
    "pytest>=7.4.0",
    # ... other dev dependencies
]
```

### Key Points:

1. **python-dotenv is optional** - Include it only in dev dependencies
2. **Core package works without .env support** - PyPI users don't need python-dotenv
3. **Environment variables always work** - No additional dependencies required
4. **Direct instantiation always works** - Full programmatic control

## Usage Patterns

### Pattern 1: Direct Python (Recommended for Libraries)

```python
from your_package import YourClass, Config

# Full programmatic control
config = Config(
    database_host="prod-db.example.com",
    database_password="secure_password_123",
    api_key="sk-prod-...",
    debug_mode=False
)

instance = YourClass(config=config)
```

### Pattern 2: Environment Variables (Recommended for Containers)

```bash
# docker-compose.yml or Kubernetes
environment:
  - DATABASE_HOST=postgres
  - DATABASE_PASSWORD=${DB_PASSWORD}
  - API_KEY=${API_KEY}
  - DEBUG_MODE=false
```

```python
from your_package import YourClass

# Automatically uses environment variables
instance = YourClass()
```

### Pattern 3: .env Files (Local Development Only)

```bash
# Install dev dependencies
pip install your-package[dev]

# Create .env file
echo "DATABASE_HOST=localhost" > .env
echo "DATABASE_PASSWORD=devpass" >> .env
echo "API_KEY=dev-key" >> .env
```

```python
from your_package import YourClass

# Automatically loads .env file
instance = YourClass()
```

## Testing Configuration

Create comprehensive tests for all three patterns:

```python
import os
import tempfile
from pathlib import Path
from your_package import Config, YourClass


def test_direct_config():
    """Test direct Python configuration."""
    config = Config(
        database_host="test-host",
        database_password="test_password_123",
        api_key="test-key"
    )
    assert config.database_host == "test-host"
    assert config.database_password == "test_password_123"
    assert config.api_key == "test-key"

    instance = YourClass(config=config)
    assert instance.get_config() == config


def test_env_vars_config():
    """Test environment variables configuration."""
    # Set environment variables
    original_env = {}
    test_env = {
        "DATABASE_HOST": "env-host",
        "DATABASE_PASSWORD": "env_password_123",
        "API_KEY": "env-key",
    }

    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        config = Config()
        assert config.database_host == "env-host"
        assert config.database_password == "env_password_123"
        assert config.api_key == "env-key"

        instance = YourClass(config=config)
        assert instance.get_config() == config
    finally:
        # Restore environment
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def test_dotenv_config():
    """Test .env file configuration."""
    # Clear relevant env vars
    env_keys = ["DATABASE_HOST", "DATABASE_PASSWORD", "API_KEY"]
    original_env = {}
    for key in env_keys:
        original_env[key] = os.environ.get(key)
        os.environ.pop(key, None)

    # Create temp .env file
    env_content = """
DATABASE_HOST=dotenv-host
DATABASE_PASSWORD=dotenv_password_123
API_KEY=dotenv-key
"""

    with tempfile.TemporaryDirectory() as temp_dir:
        env_file = Path(temp_dir) / ".env"
        env_file.write_text(env_content.strip())

        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Load .env explicitly
            from dotenv import load_dotenv
            load_dotenv(dotenv_path=str(env_file))

            config = Config()
            assert config.database_host == "dotenv-host"
            assert config.database_password == "dotenv_password_123"
            assert config.api_key == "dotenv-key"

            instance = YourClass(config=config)
            assert instance.get_config() == config
        finally:
            os.chdir(original_cwd)

    # Restore environment
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
```

## Configuration Priority

The configuration loading follows this priority order (first match wins):

1. **Explicit Config object** - When you pass `Config(...)` directly
2. **Environment Variables** - `os.getenv()` calls in Field defaults
3. **.env File** - Loaded by python-dotenv (if available)
4. **Hardcoded Defaults** - Fallback values in Field defaults

## Best Practices

1. **Use Field with default_factory** for environment variable loading
2. **Make python-dotenv optional** in dev dependencies only
3. **Provide clear documentation** for all three usage patterns
4. **Include comprehensive tests** for all configuration methods
5. **Use field validators** for input validation and security
6. **Document configuration priority** clearly
7. **Provide examples** for each usage pattern

## Migration from Single-Pattern Config

If you're migrating from a single configuration pattern:

1. **Add environment variable support** using `os.getenv()` in Field defaults
2. **Add optional .env support** with try/except import
3. **Update documentation** with all three patterns
4. **Add comprehensive tests** for new patterns
5. **Update dependency management** to make python-dotenv optional

This approach ensures backward compatibility while adding flexibility for different deployment scenarios.</content>
<parameter name="filePath">z:\code\ctx_bridge\PYDANTIC_CONFIG_GUIDE.md