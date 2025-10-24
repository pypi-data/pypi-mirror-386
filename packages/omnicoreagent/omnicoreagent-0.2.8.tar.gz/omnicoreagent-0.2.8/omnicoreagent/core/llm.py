import os
from typing import Any, Union, List
import time
import random

from dotenv import load_dotenv
import litellm
from omnicoreagent.core.utils import logger
import warnings

warnings.filterwarnings(
    "ignore", message="Pydantic serializer warnings", module="pydantic.main"
)


load_dotenv()


import logging
import os

# Environment variable
os.environ["LITELLM_LOG"] = "CRITICAL"

# Disable verbose mode
litellm.set_verbose = False

# Disable all callbacks
litellm.callbacks = []
litellm.success_callback = []
litellm.failure_callback = []

# Disable loggers
logging.getLogger("LiteLLM").disabled = True
logging.getLogger("litellm").disabled = True
logging.getLogger("litellm.proxy").disabled = True

# Set log levels to critical
for logger_name in ["LiteLLM", "litellm", "litellm.proxy"]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False


def retry_with_backoff(max_retries=3, base_delay=1, max_delay=60, backoff_factor=2):
    """Retry decorator with exponential backoff and jitter.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for delay increase
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e
                    error_msg = str(e).lower()

                    # Check if it's a retryable error
                    if any(
                        keyword in error_msg
                        for keyword in [
                            "rate limit",
                            "rate_limit",
                            "rpm",
                            "tpm",
                            "quota",
                            "throttle",
                            "too many requests",
                            "429",
                            "temporary",
                            "timeout",
                            "connection",
                        ]
                    ):
                        if attempt < max_retries:
                            # Calculate delay with exponential backoff and jitter
                            delay = min(
                                base_delay * (backoff_factor**attempt), max_delay
                            )
                            jitter = random.uniform(0, 0.1 * delay)
                            total_delay = delay + jitter

                            logger.warning(
                                f"Retryable error on attempt {attempt + 1}/{max_retries + 1}: {e}"
                            )
                            logger.info(f"Retrying in {total_delay:.2f} seconds...")

                            time.sleep(total_delay)
                            continue
                        else:
                            logger.error(
                                f"Max retries ({max_retries}) exceeded. Last error: {e}"
                            )
                    else:
                        logger.error(f"Non-retryable error: {e}")
                        break

            raise last_exception

        return wrapper

    return decorator


class LLMConnection:
    """Manages LLM connections using LiteLLM."""

    def __init__(self, config: dict[str, Any] | Any, config_filename: str):
        self.config = config
        self.config_filename = config_filename
        self.llm_config = None
        self.embedding_config = None

        if hasattr(self.config, "llm_api_key"):
            if not self.llm_config:
                logger.info("updating llm configuration")
                llm_config_result = self.llm_configuration()
                if llm_config_result:
                    logger.info(f"LLM configuration: {self.llm_config}")

                    self._set_llm_environment_variables()
                else:
                    logger.debug("LLM configuration not available or invalid")
        else:
            logger.debug("Config object doesn't have llm_api_key, skipping LLM setup")

        if (
            hasattr(self.config, "embedding_api_key")
            and self.config.embedding_api_key is not None
        ):
            if not self.embedding_config:
                try:
                    logger.info("updating embedding configuration")
                    self.embedding_configuration()
                    logger.info(f"Embedding configuration: {self.embedding_config}")

                    self._set_embedding_environment_variables()
                except Exception as e:
                    logger.warning(f"Failed to load embedding configuration: {e}")
                    self.embedding_config = None
        else:
            logger.debug(
                "Config object doesn't have embedding_api_key, skipping embedding setup"
            )

    def __str__(self):
        """Return a readable string representation of the LLMConnection."""
        config_file = self.config_filename or "default"
        return f"LLMConnection(config={config_file})"

    def __repr__(self):
        """Return a detailed representation of the LLMConnection."""
        return self.__str__()

    def get_loaded_config(self):
        """Get the already-loaded configuration without reloading it"""
        if not hasattr(self, "_loaded_config"):
            if self.config is None:
                raise ValueError("Config object is None - cannot load configuration")
            self._loaded_config = self.config.load_config(self.config_filename)
        return self._loaded_config

    def llm_configuration(self):
        """Load the LLM configuration"""

        config = self.get_loaded_config()

        if "LLM" not in config:
            logger.debug("No LLM configuration found in config file")
            return None

        llm_config = config["LLM"]
        try:
            provider = llm_config.get("provider")
            model = llm_config.get("model")

            if not provider or not model:
                logger.warning(
                    "LLM configuration missing required fields (provider or model)"
                )
                return None

            provider_model_map = {
                "openai": f"openai/{model}",
                "anthropic": f"anthropic/{model}",
                "groq": f"groq/{model}",
                "gemini": f"gemini/{model}",
                "azure": f"azure/{model}",
                "ollama": f"ollama/{model}",
            }

            provider_key = (
                provider.lower() if provider and isinstance(provider, str) else ""
            )
            full_model = provider_model_map.get(provider_key, model)

            self.llm_config = {
                "provider": provider,
                "model": full_model,
                "temperature": llm_config.get("temperature"),
                "max_tokens": llm_config.get("max_tokens"),
                "top_p": llm_config.get("top_p"),
            }

            if (
                provider
                and isinstance(provider, str)
                and provider.lower() == "azureopenai"
            ):
                azure_endpoint = llm_config.get("azure_endpoint")
                azure_api_version = llm_config.get("azure_api_version")
                azure_deployment = llm_config.get("azure_deployment")

                if azure_endpoint and isinstance(azure_endpoint, str):
                    os.environ["AZURE_API_BASE"] = azure_endpoint
                if azure_api_version and isinstance(azure_api_version, str):
                    os.environ["AZURE_API_VERSION"] = azure_api_version
                if azure_deployment and isinstance(azure_deployment, str):
                    self.llm_config["model"] = f"azure/{azure_deployment}"

            if provider and isinstance(provider, str) and provider.lower() == "ollama":
                ollama_host = llm_config.get("ollama_host")
                if ollama_host and isinstance(ollama_host, str):
                    os.environ["OLLAMA_API_BASE"] = ollama_host

            return self.llm_config
        except Exception as e:
            logger.error(f"Error loading LLM configuration: {e}")
            return None

    def embedding_configuration(self):
        """Load the embedding configuration"""

        config = self.get_loaded_config()

        try:
            embedding_config = config.get("EMBEDDING", {})
            if not embedding_config:
                logger.debug("No EMBEDDING configuration found in config file")
                return None
            provider = embedding_config.get("provider")
            model = embedding_config.get("model")
            dimensions = embedding_config.get("dimensions")

            required_keys = ["provider", "model", "dimensions"]
            missing_keys = [
                key for key in required_keys if not embedding_config.get(key)
            ]

            if missing_keys:
                logger.warning(
                    f"Embedding configuration missing required fields: {', '.join(missing_keys)}"
                )
                raise ValueError(
                    f"Missing required embedding configuration fields: {', '.join(missing_keys)}"
                )

            dimensions = embedding_config.get("dimensions")
            if not isinstance(dimensions, int) or dimensions <= 0:
                logger.warning(
                    "Embedding configuration 'dimensions' must be a positive integer"
                )
                return ValueError("Invalid 'dimensions' in embedding configuration")

            provider_model_map = {
                "openai": f"openai/{model}",
                "cohere": f"cohere/{model}",
                "mistral": f"mistral/{model}",
                "gemini": f"gemini/{model}",
                "vertex_ai": f"vertex_ai/{model}",
                "voyage": f"voyage/{model}",
                "nebius": f"nebius/{model}",
                "nvidia_nim": f"nvidia_nim/{model}",
                "bedrock": f"bedrock/{model}",
                "huggingface": f"huggingface/{model}",
            }

            provider_key = (
                provider.lower() if provider and isinstance(provider, str) else ""
            )
            full_model = provider_model_map.get(provider_key, model)

            self.embedding_config = {
                "provider": provider,
                "model": full_model,
                "dimensions": embedding_config.get("dimensions"),
                "encoding_format": embedding_config.get("encoding_format"),
                "timeout": embedding_config.get("timeout"),
            }

            if (
                provider
                and isinstance(provider, str)
                and provider.lower() == "azureopenai"
            ):
                azure_endpoint = embedding_config.get("azure_endpoint")
                azure_api_version = embedding_config.get("azure_api_version")
                azure_deployment = embedding_config.get("azure_deployment")

                if azure_endpoint and isinstance(azure_endpoint, str):
                    os.environ["AZURE_API_BASE"] = azure_endpoint
                if azure_api_version and isinstance(azure_api_version, str):
                    os.environ["AZURE_API_VERSION"] = azure_api_version
                if azure_deployment and isinstance(azure_deployment, str):
                    self.embedding_config["model"] = f"azure/{azure_deployment}"

            elif provider.lower() == "vertex_ai":
                vertex_project = embedding_config.get("vertex_project")
                vertex_location = embedding_config.get("vertex_location")

                if vertex_project and isinstance(vertex_project, str):
                    litellm.vertex_project = vertex_project
                if vertex_location and isinstance(vertex_location, str):
                    litellm.vertex_location = vertex_location

            elif provider.lower() == "nvidia_nim":
                nvidia_nim_api_base = embedding_config.get("nvidia_nim_api_base")
                if nvidia_nim_api_base and isinstance(nvidia_nim_api_base, str):
                    os.environ["NVIDIA_NIM_API_BASE"] = nvidia_nim_api_base

            elif provider.lower() == "bedrock":
                aws_region = embedding_config.get("aws_region")
                if aws_region:
                    os.environ["AWS_REGION_NAME"] = aws_region

            return self.embedding_config

        except Exception as e:
            logger.error(f"Error loading embedding configuration: {e}")
            return None

    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=30)
    async def embedding_call(
        self,
        input_text: Union[str, List[str]],
        input_type: str = None,
        metadata: dict = None,
        user: str = None,
    ):
        """Call the embedding service using LiteLLM"""
        try:
            if not self.embedding_config:
                logger.error("Embedding configuration not loaded")
                return None

            if not self.embedding_config.get(
                "provider"
            ) or not self.embedding_config.get("model"):
                logger.error("Embedding provider or model not configured")
                return None

            params = {
                "model": self.embedding_config["model"],
                "input": input_text,
            }

            if self.embedding_config.get("dimensions") is not None:
                params["dimensions"] = self.embedding_config["dimensions"]

            encoding_format = self.embedding_config.get("encoding_format")
            if encoding_format is None:
                if self.embedding_config["provider"].lower() == "voyage":
                    encoding_format = "base64"
                else:
                    encoding_format = "float"

            params["encoding_format"] = encoding_format

            if self.embedding_config.get("timeout") is not None:
                params["timeout"] = self.embedding_config["timeout"]

            if input_type:
                params["input_type"] = input_type

            if metadata:
                params["metadata"] = metadata

            if user:
                params["user"] = user

            provider = self.embedding_config["provider"].lower()

            if provider == "cohere" and not input_type:
                params["input_type"] = "search_document"

            litellm.drop_params = True

            response = await litellm.aembedding(**params)
            return response

        except Exception as e:
            error_message = f"Error calling embedding service with model {self.embedding_config.get('model')}: {e}"
            logger.error(error_message)
            return None

    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=30)
    def embedding_call_sync(
        self,
        input_text: Union[str, List[str]],
        input_type: str = None,
        metadata: dict = None,
        user: str = None,
    ):
        """Synchronous call to the embedding service using LiteLLM"""
        try:
            if not self.embedding_config:
                logger.error("Embedding configuration not loaded")
                return None

            if not self.embedding_config.get(
                "provider"
            ) or not self.embedding_config.get("model"):
                logger.error("Embedding provider or model not configured")
                return None

            params = {
                "model": self.embedding_config["model"],
                "input": input_text,
            }

            if self.embedding_config.get("dimensions") is not None:
                params["dimensions"] = self.embedding_config["dimensions"]

            encoding_format = self.embedding_config.get("encoding_format")
            if encoding_format is None:
                if self.embedding_config["provider"].lower() == "voyage":
                    encoding_format = "base64"
                else:
                    encoding_format = "float"

            params["encoding_format"] = encoding_format

            if self.embedding_config.get("timeout") is not None:
                params["timeout"] = self.embedding_config["timeout"]

            if input_type:
                params["input_type"] = input_type

            if metadata:
                params["metadata"] = metadata

            if user:
                params["user"] = user

            provider = self.embedding_config["provider"].lower()

            if provider == "cohere" and not input_type:
                params["input_type"] = "search_document"

            litellm.drop_params = True

            response = litellm.embedding(**params)
            return response

        except Exception as e:
            error_message = f"Error calling embedding service with model {self.embedding_config.get('model')}: {e}"
            logger.error(error_message)
            return None

    def _set_llm_environment_variables(self):
        """Set environment variables only for the configured LLM provider."""
        if not self.llm_config or not self.llm_config.get("provider"):
            return

        provider = self.llm_config["provider"].lower()
        api_key = self.config.llm_api_key

        if provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "anthropic":
            os.environ["ANTHROPIC_API_KEY"] = api_key
        elif provider == "groq":
            os.environ["GROQ_API_KEY"] = api_key
        elif provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
        elif provider == "deepseek":
            os.environ["DEEPSEEK_API_KEY"] = api_key
        elif provider == "openrouter":
            os.environ["OPENROUTER_API_KEY"] = api_key
        elif provider == "azure" or provider == "azureopenai":
            os.environ["AZURE_API_KEY"] = api_key

        logger.debug(f"Set environment variable for LLM provider: {provider}")

    def _set_embedding_environment_variables(self):
        """Set environment variables only for the configured embedding provider."""
        if not self.embedding_config or not self.embedding_config.get("provider"):
            return

        provider = self.embedding_config["provider"].lower()
        api_key = self.config.embedding_api_key

        if provider == "openai":
            os.environ["OPENAI_API_KEY"] = api_key
        elif provider == "cohere":
            os.environ["COHERE_API_KEY"] = api_key
        elif provider == "huggingface":
            os.environ["HUGGINGFACE_API_KEY"] = api_key
        elif provider == "mistral":
            os.environ["MISTRAL_API_KEY"] = api_key
        elif provider == "voyage":
            os.environ["VOYAGE_API_KEY"] = api_key
        elif provider == "nebius":
            os.environ["NEBIUS_API_KEY"] = api_key
        elif provider == "nvidia_nim":
            os.environ["NVIDIA_NIM_API_KEY"] = api_key
        elif provider == "gemini":
            os.environ["GEMINI_API_KEY"] = api_key
        elif provider == "bedrock":
            pass
        elif provider == "vertex_ai":
            pass

        logger.debug(f"Set environment variable for embedding provider: {provider}")

    def is_embedding_available(self) -> bool:
        """Check if embedding functionality is available (API key is set)"""
        return (
            hasattr(self.config, "embedding_api_key")
            and self.config.embedding_api_key is not None
        )

    def is_llm_available(self) -> bool:
        """Check if LLM functionality is available (API key is set)"""
        return (
            hasattr(self.config, "llm_api_key") and self.config.llm_api_key is not None
        )

    def to_dict(self, msg):
        if hasattr(msg, "model_dump"):
            msg_dict = msg.model_dump(exclude_none=True)

            if "timestamp" in msg_dict and hasattr(msg_dict["timestamp"], "timestamp"):
                msg_dict["timestamp"] = msg_dict["timestamp"].timestamp()
            elif "timestamp" in msg_dict and hasattr(msg_dict["timestamp"], "tzinfo"):
                msg_dict["timestamp"] = msg_dict["timestamp"].timestamp()
            return msg_dict
        elif isinstance(msg, dict):
            return msg
        elif hasattr(msg, "__dict__"):
            return {k: v for k, v in msg.__dict__.items() if v is not None}
        else:
            return msg

    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=30)
    async def llm_call(
        self,
        messages: list[Any],
        tools: list[dict[str, Any]] = None,
    ):
        """Call the LLM using LiteLLM"""
        try:
            if not self.llm_config:
                logger.debug("LLM configuration not loaded, skipping LLM call")
                return None

            messages_dicts = [self.to_dict(m) for m in messages]

            params = {
                "model": self.llm_config["model"],
                "messages": messages_dicts,
            }

            if self.llm_config.get("temperature") is not None:
                params["temperature"] = self.llm_config["temperature"]

            if self.llm_config.get("max_tokens") is not None:
                params["max_tokens"] = self.llm_config["max_tokens"]

            if self.llm_config.get("top_p") is not None:
                params["top_p"] = self.llm_config["top_p"]

            # Add tools if provided
            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            if self.llm_config["provider"].lower() == "openrouter":
                if not tools:
                    params["stop"] = ["\n\nObservation:"]

            litellm.drop_params = True

            response = await litellm.acompletion(**params)
            return response

        except Exception as e:
            error_message = (
                f"Error calling LLM with model {self.llm_config.get('model')}: {e}"
            )
            logger.error(error_message)
            return None

    @retry_with_backoff(max_retries=3, base_delay=1, max_delay=30)
    def llm_call_sync(
        self,
        messages: list[Any],
        tools: list[dict[str, Any]] = None,
    ):
        """Synchronous call to the LLM using LiteLLM"""
        try:
            if not self.llm_config:
                logger.debug("LLM configuration not loaded, skipping LLM call")
                return None

            messages_dicts = [self.to_dict(m) for m in messages]

            params = {
                "model": self.llm_config["model"],
                "messages": messages_dicts,
            }

            if self.llm_config.get("temperature") is not None:
                params["temperature"] = self.llm_config["temperature"]

            if self.llm_config.get("max_tokens") is not None:
                params["max_tokens"] = self.llm_config["max_tokens"]

            if self.llm_config.get("top_p") is not None:
                params["top_p"] = self.llm_config["top_p"]

            if tools:
                params["tools"] = tools
                params["tool_choice"] = "auto"

            if self.llm_config["provider"].lower() == "openrouter":
                if not tools:
                    params["stop"] = ["\n\nObservation:"]

            litellm.drop_params = True

            response = litellm.completion(**params)
            return response

        except Exception as e:
            error_message = (
                f"Error calling LLM with model {self.llm_config.get('model')}: {e}"
            )
            logger.error(error_message)
            return None
