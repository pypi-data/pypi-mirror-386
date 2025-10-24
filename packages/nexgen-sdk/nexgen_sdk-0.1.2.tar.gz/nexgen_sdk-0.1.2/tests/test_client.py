"""
Tests for AI SDK Client
"""

import pytest
from unittest.mock import Mock, patch
from ..ai_sdk import AISDKClient
from ..ai_sdk.exceptions import AISDKException, AuthenticationException
from ..ai_sdk.core.config import Config


def test_client_initialization():
    """Test basic client initialization."""
    client = AISDKClient(
        api_key="test-key",
        provider="openai",
        base_url="https://api.openai.com/v1"
    )
    
    assert client._config.api_key == "test-key"
    assert client._provider_name == "openai"
    assert client._config.base_url == "https://api.openai.com/v1"


def test_client_initialization_with_defaults():
    """Test client initialization with default values."""
    client = AISDKClient(api_key="test-key")
    
    assert client._config.api_key == "test-key"
    assert client._provider_name == "openai"
    assert client._config.base_url == "https://api.openai.com/v1"
    assert client._config.timeout == 30.0


def test_builder_pattern():
    """Test client builder pattern."""
    client = (AISDKClient.builder()
               .with_api_key("builder-key")
               .with_provider("vllm")
               .with_base_url("https://custom.url")
               .with_timeout(60.0)
               .build())
    
    assert client._config.api_key == "builder-key"
    assert client._provider_name == "vllm"
    assert client._config.base_url == "https://custom.url"
    assert client._config.timeout == 60.0


def test_chat_interface():
    """Test chat interface creation."""
    client = AISDKClient(api_key="test-key")
    
    chat = client.chat()
    assert chat is not None
    assert hasattr(chat, 'create')


def test_completions_interface():
    """Test completions interface creation."""
    client = AISDKClient(api_key="test-key")
    
    completions = client.completions()
    assert completions is not None
    assert hasattr(completions, 'create')


def test_embeddings_interface():
    """Test embeddings interface creation."""
    client = AISDKClient(api_key="test-key")
    
    embeddings = client.embeddings()
    assert embeddings is not None
    assert hasattr(embeddings, 'create')


def test_config_from_environment():
    """Test configuration from environment variables."""
    with patch.dict('os.environ', {
        'AI_SDK_API_KEY': 'env-key',
        'AI_SDK_BASE_URL': 'https://env.url',
        'AI_SDK_TIMEOUT': '45.0'
    }):
        config = Config.from_environment()
        assert config.api_key == 'env-key'
        assert config.base_url == 'https://env.url'
        assert config.timeout == 45.0


def test_config_from_dict():
    """Test configuration from dictionary."""
    config_dict = {
        'api_key': 'dict-key',
        'base_url': 'https://dict.url',
        'timeout': 60.0,
        'custom_option': 'custom_value'
    }
    
    config = Config.from_dict(config_dict)
    assert config.api_key == 'dict-key'
    assert config.base_url == 'https://dict.url'
    assert config.timeout == 60.0
    assert config.get('custom_option') == 'custom_value'


@patch('ai_sdk.providers.base.ProviderFactory.create_provider')
def test_provider_creation(mock_create_provider):
    """Test provider creation during client initialization."""
    mock_provider = Mock()
    mock_create_provider.return_value = mock_provider
    
    client = AISDKClient(api_key="test-key", provider="vllm")
    
    mock_create_provider.assert_called_once_with("vllm", client._config, http_client=None)
    assert client._provider == mock_provider


def test_client_close():
    """Test client resource cleanup."""
    client = AISDKClient(api_key="test-key")
    client._provider = Mock()
    
    client.close()
    client._provider.close.assert_called_once()


def test_client_context_manager():
    """Test client as context manager."""
    with AISDKClient(api_key="test-key") as client:
        assert client is not None
        client._provider = Mock()
    
    # Provider should be closed when exiting context
    client._provider.close.assert_called_once()


@pytest.mark.asyncio
async def test_async_functionality():
    """Test that async functionality is properly supported."""
    # This is a placeholder for async tests
    # Add actual async tests when implementing async support
    pass