from typing import Any
from unittest.mock import Mock, patch

from any_llm.api import completion
from any_llm.constants import LLMProvider


def test_completion_extracts_all_config_from_kwargs() -> None:
    """Test that api_key and api_base are properly extracted from kwargs to create config."""
    mock_provider = Mock()
    mock_provider.completion.return_value = Mock()

    with patch("any_llm.any_llm.AnyLLM.create") as mock_create:
        mock_create.return_value = mock_provider
        kwargs: dict[str, Any] = {
            "other_param": "value",
        }
        completion(
            model="mistral/mistral-small",
            messages=[{"role": "user", "content": "Hello"}],
            api_key="test_key",
            api_base="https://test.com",
            **kwargs,
        )

        mock_create.assert_called_once_with(LLMProvider.MISTRAL, api_key="test_key", api_base="https://test.com")

        mock_provider.completion.assert_called_once()
        _, kwargs = mock_provider.completion.call_args
        assert kwargs["model"] == "mistral-small"
        assert kwargs["messages"] == [{"role": "user", "content": "Hello"}]
        assert kwargs["other_param"] == "value"


def test_completion_extracts_partial_config_from_kwargs() -> None:
    """Test that only present config parameters are extracted."""
    mock_provider = Mock()
    mock_provider.completion.return_value = Mock()

    with patch("any_llm.any_llm.AnyLLM.create") as mock_create:
        mock_create.return_value = mock_provider

        completion(
            model="mistral/mistral-small",
            messages=[{"role": "user", "content": "Hello"}],
            api_key="test_key",
            other_param="value",
        )

        mock_create.assert_called_once_with(LLMProvider.MISTRAL, api_key="test_key", api_base=None)

        mock_provider.completion.assert_called_once()
        _, kwargs = mock_provider.completion.call_args
        assert kwargs["model"] == "mistral-small"
        assert kwargs["messages"] == [{"role": "user", "content": "Hello"}]
        assert kwargs["other_param"] == "value"


def test_completion_no_config_extraction() -> None:
    """Test that empty config is created when no config parameters are provided."""
    mock_provider = Mock()
    mock_provider.completion.return_value = Mock()

    with patch("any_llm.any_llm.AnyLLM.create") as mock_create:
        mock_create.return_value = mock_provider

        kwargs: dict[str, Any] = {
            "other_param": "value",
        }
        completion(model="mistral/mistral-small", messages=[{"role": "user", "content": "Hello"}], **kwargs)

        mock_create.assert_called_once_with(LLMProvider.MISTRAL, api_key=None, api_base=None)

        mock_provider.completion.assert_called_once()
        _, kwargs = mock_provider.completion.call_args
        assert kwargs["model"] == "mistral-small"
        assert kwargs["messages"] == [{"role": "user", "content": "Hello"}]
        assert kwargs["other_param"] == "value"


def test_completion_extracts_api_base_only() -> None:
    """Test that only api_base is extracted when only it's provided."""
    mock_provider = Mock()
    mock_provider.completion.return_value = Mock()

    with patch("any_llm.any_llm.AnyLLM.create") as mock_create:
        mock_create.return_value = mock_provider

        completion(
            model="ollama/llama2",
            messages=[{"role": "user", "content": "Test"}],
            api_base="https://custom-endpoint.com",
        )

        mock_create.assert_called_once_with(LLMProvider.OLLAMA, api_key=None, api_base="https://custom-endpoint.com")

        mock_provider.completion.assert_called_once()
        _, kwargs = mock_provider.completion.call_args
        assert kwargs["model"] == "llama2"
        assert kwargs["messages"] == [{"role": "user", "content": "Test"}]
