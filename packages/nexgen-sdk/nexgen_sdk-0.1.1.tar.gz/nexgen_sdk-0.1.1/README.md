# AI SDK Python

A comprehensive Python SDK for interacting with AI models, compatible with OpenAI's API format and supporting multiple providers.

## Features

- 🤖 **Multiple Provider Support**: OpenAI, LiteLLM, and VLLM providers
- 🔄 **Streaming Support**: Real-time streaming responses with event handling
- 🛡️ **Error Handling**: Comprehensive error handling with custom exceptions
- 🔧 **Flexible Configuration**: Environment variables, config files, and programmatic setup
- 📦 **Easy Integration**: Simple, intuitive API design
- 🎯 **Type Safety**: Full type hints support

## Installation

```bash
pip install nexgen-sdk
```

For development:
```bash
pip install nexgen-sdk[dev]
```

## Quick Start

### Basic Usage

```python
from ai_sdk import AISDKClient

# Initialize client
client = AISDKClient(
    api_key="your-api-key",
    provider="openai"  # or "vllm", "litellm"
)

# Create chat completion
response = client.chat().create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "Hello, world!"}
    ]
)

print(response['choices'][0]['message']['content'])
```

### Streaming

```python
# Stream responses in real-time
response = client.chat().create(
    model="gpt-3.5-turbo",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in response:
    if chunk['choices'][0]['delta'].get('content'):
        print(chunk['choices'][0]['delta']['content'], end='', flush=True)
```

### Provider-Specific Examples

#### VLLM Provider with New Format
```python
client = AISDKClient(provider="vllm", api_key="your-key")

# New format supports complex user content objects
response = client.chat().create(
    system_prompt="You are a helpful AI assistant",
    messages=[
        {
            "role": "user",
            "content": {
                "query": "What is Python?",
                "detail_level": "intermediate",
                "include_examples": True
            }
        }
    ],
    model="model_name"
)
```

## Configuration

### Environment Variables
```bash
export AI_SDK_API_KEY="your-api-key"
export AI_SDK_BASE_URL="https://api.openai.com/v1"
export AI_SDK_TIMEOUT="30.0"
```

### Builder Pattern
```python
client = (AISDKClient.builder()
           .with_provider("vllm")
           .with_api_key("your-key")
           .with_base_url("https://your-vllm-endpoint")
           .with_timeout(60.0)
           .build())
```

## Providers

### OpenAI Provider
- **Base URL**: `https://api.openai.com/v1`
- **Models**: GPT-3.5, GPT-4, and all OpenAI models
- **Features**: Chat, completions, embeddings

### VLLM Provider
- **Custom Endpoints**: Supports any VLLM deployment
- **New Format**: Enhanced message format with complex user content
- **Streaming**: Optimized real-time streaming

### LiteLLM Provider
- **Unified Interface**: Access 100+ models through LiteLLM
- **Model Support**: OpenAI, Anthropic, Cohere, and more
- **Fallback**: Automatic fallback between providers

## API Reference

### Client
- `AISDKClient()` - Main client class
- `chat()` - Access chat completions
- `completions()` - Access text completions  
- `embeddings()` - Access embeddings

### Chat Completions
- `create()` - Create chat completion or stream
- Parameters: `messages`, `model`, `temperature`, `stream`, etc.

### Error Handling
```python
from ai_sdk.exceptions import (
    AISDKException,
    APIException,
    AuthenticationException,
    RateLimitException
)

try:
    response = client.chat().create(...)
except AuthenticationException:
    print("Invalid API key")
except RateLimitException:
    print("Rate limit exceeded")
except AISDKException as e:
    print(f"SDK Error: {e}")
```

## Development

### Setup
```bash
git clone https://github.com/Dhruv1969Karnwal/ai-sdk-python
cd ai-sdk-python
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black ai_sdk
flake8 ai_sdk
mypy ai_sdk
```

## Examples

See the `examples/` directory for comprehensive usage examples:

- `new_format_example.py` - VLLM new format examples
- `debug_streaming.py` - Streaming debug examples
- `test_clean_streaming.py` - Clean streaming tests

## Requirements

- Python 3.7+
- httpx>=0.23.0
- typing_extensions>=3.7.4 (Python < 3.8)

### Optional Dependencies
- litellm>=1.0.0 (for LiteLLM provider)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://ai-sdk.readthedocs.io)
- 🐛 [Issues](https://github.com/Dhruv1969Karnwal/ai-sdk-python/issues)
- 💬 [Discussions](https://github.com/Dhruv1969Karnwal/ai-sdk-python/discussions)

## Contributing

Contributions are welcome! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.