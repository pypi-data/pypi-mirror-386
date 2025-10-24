t# Pydantic AI Claude Code

Use your local Claude Code CLI as a Pydantic AI model provider.

This package provides a Pydantic AI-compatible model implementation that wraps the local Claude CLI, enabling you to use Claude locally with all Pydantic AI features including structured responses, tool calling, streaming, and multi-turn conversations.

## Features

- **Full Pydantic AI Compatibility**: Drop-in replacement for any Pydantic AI model
- **Structured Responses**: Get validated, typed responses using Pydantic models
- **Custom Tool Calling**: Use your own Python functions as tools
- **True Streaming**: Real-time response streaming via Claude CLI's stream-json mode
- **Local Execution**: All processing happens locally on your machine
- **Session Persistence**: Maintain conversation context across multiple requests
- **Additional Files**: Provide local files for Claude to read and analyze
- **Automatic Response Saving**: Raw prompts and responses saved for debugging
- **Configurable**: Fine-tune permissions, working directories, and tool access

## Installation

```bash
# Using uv (recommended)
uv add pydantic-ai-claude-code

# Using pip
pip install pydantic-ai-claude-code
```

**Prerequisites**:
- [Claude Code CLI](https://claude.com/claude-code) must be installed and authenticated
- **Sandbox Runtime** (required): `npm install -g @anthropic-ai/sandbox-runtime`

## Sandbox Mode (Enabled by Default)

**New in v0.8.0**: All Claude Code execution now runs in a secure sandbox by default using Anthropic's [`sandbox-runtime`](https://github.com/anthropic-experimental/sandbox-runtime).

### What This Means

- **OS-Level Isolation**: Uses bubblewrap (Linux) or sandbox-exec (macOS) for kernel-level security
- **Filesystem Access**: Full read/write access to `/tmp` only - everything else is read-only
- **Network Access**: Restricted to `api.anthropic.com` for Claude API calls
- **Autonomous Execution**: `IS_SANDBOX=1` environment variable enables Claude to run without permission prompts
- **Zero Configuration**: Works automatically after installing `sandbox-runtime`

### Installation

```bash
# Install sandbox-runtime globally via npm
npm install -g @anthropic-ai/sandbox-runtime

# Verify installation
srt --version
```

### Disabling Sandbox (Not Recommended)

If you need to disable sandbox mode for debugging:

```python
from pydantic_ai_claude_code import ClaudeCodeProvider
from pydantic_ai import Agent

provider = ClaudeCodeProvider({"use_sandbox_runtime": False})
agent = Agent('claude-code:sonnet')
```

⚠️ **Warning**: Disabling sandbox removes security isolation. Only do this in trusted environments.

## Quick Start

### Basic Usage (String Format - Simplest!)

```python
import pydantic_ai_claude_code  # Register the provider

from pydantic_ai import Agent

# Just use the string format - easiest way!
agent = Agent('claude-code:sonnet')

# Run a simple query
result = agent.run_sync("What is 2+2?")
print(result.output)  # Output: 4
```

### Structured Responses

```python
import pydantic_ai_claude_code

from pydantic import BaseModel
from pydantic_ai import Agent

class Analysis(BaseModel):
    complexity: int  # 1-10
    maintainability: str
    suggestions: list[str]

# String format works with all Pydantic AI features
agent = Agent('claude-code:sonnet', output_type=Analysis)

result = agent.run_sync("Analyze this code: def foo(): pass")
print(f"Complexity: {result.output.complexity}")
```

### Custom Tools

```python
import pydantic_ai_claude_code

from pydantic_ai import Agent

def get_weather(city: str) -> str:
    """Get weather for a city."""
    return f"Weather in {city}: Sunny, 22°C"

agent = Agent(
    'claude-code:sonnet',
    tools=[get_weather],
)

result = agent.run_sync("What's the weather in Paris?")
print(result.output)
```

### Streaming

```python
import pydantic_ai_claude_code

from pydantic_ai import Agent

agent = Agent('claude-code:sonnet')

async with agent.run_stream('Write a haiku about code') as result:
    async for text in result.stream_text():
        print(text, end='', flush=True)
```

## Advanced Configuration

When you need fine-grained control, use the explicit model and provider:

```python
from pydantic_ai import Agent
from pydantic_ai_claude_code import ClaudeCodeModel, ClaudeCodeProvider

# Custom provider with specific settings
provider = ClaudeCodeProvider(
    working_directory="/path/to/project",
    allowed_tools=["Read", "Edit", "Grep"],  # Restrict tool access
    permission_mode="acceptEdits",
    use_temp_workspace=False,  # Use specific directory instead of /tmp
)

model = ClaudeCodeModel("sonnet", provider=provider)
agent = Agent(model)

result = agent.run_sync("Analyze the codebase structure")
```

### Temporary Workspace

```python
from pydantic_ai_claude_code import ClaudeCodeModel, ClaudeCodeProvider

# Create isolated workspace that auto-cleans
with ClaudeCodeProvider(use_temp_workspace=True) as provider:
    model = ClaudeCodeModel("sonnet", provider=provider)
    agent = Agent(model)
    result = agent.run_sync("Create a test file")
# Workspace automatically cleaned up
```

### Providing Additional Files

Provide local files for Claude to read and analyze:

```python
from pathlib import Path
from pydantic_ai import Agent

agent = Agent('claude-code:sonnet')

result = agent.run_sync(
    "Read utils.py and config.json. Summarize what they configure.",
    model_settings={
        "additional_files": {
            "utils.py": Path("src/utils.py"),           # Copy single file
            "config.json": Path("config/prod.json"),    # From different location
            "docs/spec.md": Path("specs/feature.md"),   # Into subdirectory
        }
    }
)
```

Files are copied into the working directory before execution, and Claude can reference them directly:

- `"Read utils.py"`
- `"Read config.json"`
- `"Read docs/spec.md"`

Each execution gets its own numbered subdirectory with isolated file copies.

### Binary Content (Standard Interface)

Use Pydantic AI's standard `BinaryContent` interface to attach images, PDFs, and other binary files. This works identically across all model providers:

```python
from pathlib import Path
from pydantic_ai import Agent, BinaryContent

agent = Agent('claude-code:sonnet')

# Send an image from file
image_data = Path('photo.jpg').read_bytes()
result = agent.run_sync(
    [
        'What is in this image?',
        BinaryContent(data=image_data, media_type='image/jpeg'),
    ]
)

# Send a PDF document
pdf_data = Path('document.pdf').read_bytes()
result = agent.run_sync(
    [
        'Summarize this document:',
        BinaryContent(data=pdf_data, media_type='application/pdf'),
    ]
)

# Compare multiple images
result = agent.run_sync(
    [
        'Compare these images:',
        BinaryContent(data=image1_data, media_type='image/png'),
        'and',
        BinaryContent(data=image2_data, media_type='image/jpeg'),
    ]
)
```

**How it works:**

- Binary content is automatically written to files in the working directory
- Files are referenced in the prompt (e.g., `[Image: filename.png]`)
- Claude Code CLI can then read the files directly
- No Claude Code-specific code needed - this is standard Pydantic AI!

**Supported formats:**
- Images: PNG, JPEG, GIF, WebP, etc.
- Documents: PDF, TXT, JSON, etc.
- Audio: MP3, WAV, etc.
- Video: MP4, WebM, etc.

**Benefits:**
- **Portable code** - works with OpenAI, Anthropic, Google, and Claude Code
- **Standard interface** - same `BinaryContent` class for all providers
- **No provider lock-in** - switch between cloud and local with one line change

### Error Handling

#### OAuth Token Expiration

For long-running processes (>7 hours), OAuth tokens may expire. Handle gracefully with `ClaudeOAuthError`:

```python
from pydantic_ai import Agent
from pydantic_ai_claude_code import ClaudeOAuthError

agent = Agent('claude-code:sonnet')

try:
    result = agent.run_sync("Process large dataset")
except ClaudeOAuthError as e:
    print(f"Authentication expired: {e}")
    print(f"Please run: {e.reauth_instruction}")  # "Please run /login"
    # Prompt user to re-authenticate, then retry
except RuntimeError as e:
    # Handle other CLI errors
    print(f"CLI error: {e}")
```

**For batch processing with automatic retry:**

```python
from pydantic_ai_claude_code import ClaudeOAuthError
import time

def process_batch_with_retry(items, max_auth_retries=3):
    """Process items with OAuth re-authentication support."""
    results = []

    for item in items:
        auth_retries = 0
        while auth_retries < max_auth_retries:
            try:
                result = agent.run_sync(f"Process: {item}")
                results.append(result.output)
                break  # Success

            except ClaudeOAuthError as e:
                auth_retries += 1
                print(f"\n{'='*60}")
                print(f"OAuth token expired: {e.reauth_instruction}")
                print(f"{'='*60}\n")

                if auth_retries >= max_auth_retries:
                    raise  # Give up after max retries

                input("Press Enter after running /login to continue...")
                time.sleep(2)  # Brief pause before retry

    return results
```

### Logging

The package uses Python's standard logging module. To enable debug logging in your application:

```python
import logging

# Enable debug logging for pydantic-ai-claude-code
logging.basicConfig(level=logging.DEBUG)
logging.getLogger('pydantic_ai_claude_code').setLevel(logging.DEBUG)

# Or just for specific components
logging.getLogger('pydantic_ai_claude_code.model').setLevel(logging.DEBUG)
logging.getLogger('pydantic_ai_claude_code.utils').setLevel(logging.INFO)
```

This will log:

- Model initialization and configuration
- CLI command execution and responses
- Message formatting and conversion
- Tool call parsing and execution
- Structured output handling
- Streaming events and completion

## Available Models

- `claude-code:sonnet` - Claude 3.5 Sonnet (default, recommended)
- `claude-code:opus` - Claude 3 Opus (most capable)
- `claude-code:haiku` - Claude 3.5 Haiku (fastest)

Or use full model names like `claude-code:claude-sonnet-4-5-20250929`

## Integration with Existing Projects

Replace your current LLM calls with Claude Code:

**Before:**

```python
agent = Agent('openai:gpt-4o')
# or
agent = Agent('anthropic:claude-3-5-sonnet-latest')
```

**After:**

```python
import pydantic_ai_claude_code  # Add this import

agent = Agent('claude-code:sonnet')  # Change this line
```

Everything else stays the same! All your tools, structured outputs, dependencies, and streaming code works identically.

## Key Differences from Cloud Providers

| Aspect | Cloud Providers | Claude Code Local |
|--------|----------------|-------------------|
| **Execution** | Remote API calls | Local on your machine |
| **Cost** | Per-token pricing | Uses Claude desktop subscription |
| **Data Privacy** | Data sent to cloud | Data stays local |
| **Speed** | Network latency | Local execution |
| **API Key** | Required | Not needed (uses local auth) |

## Examples

See the `examples/` directory for more demonstrations:

- `basic_example.py` - Simple queries and usage tracking
- `structured_example.py` - Structured output with Pydantic models
- `async_example.py` - Async/await usage patterns
- `advanced_example.py` - Custom provider configurations
- `tools_and_streaming.py` - Custom tools and streaming responses
- `sandbox_example.py` - Sandbox-runtime integration for production security
- `binary_content_example.py` - Standard interface for images, PDFs, and binary files
- `additional_files_example.py` - Providing local files for analysis (Claude Code-specific)

## License

MIT License
