from _typeshed import Incomplete
from gllm_core.event import EventEmitter as EventEmitter
from gllm_core.schema.tool import Tool
from gllm_core.utils.retry import RetryConfig as RetryConfig
from gllm_inference.constants import GOOGLE_SCOPES as GOOGLE_SCOPES, SECONDS_TO_MILLISECONDS as SECONDS_TO_MILLISECONDS
from gllm_inference.exceptions import BaseInvokerError as BaseInvokerError, convert_http_status_to_base_invoker_error as convert_http_status_to_base_invoker_error
from gllm_inference.exceptions.provider_error_map import GOOGLE_ERROR_MAPPING as GOOGLE_ERROR_MAPPING
from gllm_inference.lm_invoker.lm_invoker import BaseLMInvoker as BaseLMInvoker
from gllm_inference.lm_invoker.schema.google import InputType as InputType, Key as Key
from gllm_inference.schema import Attachment as Attachment, AttachmentType as AttachmentType, LMOutput as LMOutput, Message as Message, MessageRole as MessageRole, ModelId as ModelId, ModelProvider as ModelProvider, Reasoning as Reasoning, ResponseSchema as ResponseSchema, ThinkingEvent as ThinkingEvent, TokenUsage as TokenUsage, ToolCall as ToolCall, ToolResult as ToolResult
from langchain_core.tools import Tool as LangChainTool
from typing import Any

SUPPORTED_ATTACHMENTS: Incomplete
DEFAULT_THINKING_BUDGET: int
REQUIRE_THINKING_MODEL_PREFIX: Incomplete
IMAGE_GENERATION_MODELS: Incomplete
YOUTUBE_URL_PATTERN: Incomplete

class GoogleLMInvoker(BaseLMInvoker):
    '''A language model invoker to interact with Google language models.

    Attributes:
        model_id (str): The model ID of the language model.
        model_provider (str): The provider of the language model.
        model_name (str): The name of the language model.
        client_params (dict[str, Any]): The Google client instance init parameters.
        default_hyperparameters (dict[str, Any]): Default hyperparameters for invoking the model.
        tools (list[Any]): The list of tools provided to the model to enable tool calling.
        response_schema (ResponseSchema | None): The schema of the response. If provided, the model will output a
            structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema dictionary.
        output_analytics (bool): Whether to output the invocation analytics.
        retry_config (RetryConfig | None): The retry configuration for the language model.
        generate_image (bool): Whether to generate image. Only allowed for image generation models.
        thinking (bool): Whether to enable thinking. Only allowed for thinking models.
        thinking_budget (int): The tokens allowed for thinking process. Only allowed for thinking models.
            If set to -1, the model will control the budget automatically.

    Basic usage:
        The `GoogleLMInvoker` can be used as follows:
        ```python
        lm_invoker = GoogleLMInvoker(model_name="gemini-2.5-flash")
        result = await lm_invoker.invoke("Hi there!")
        ```

    Authentication:
        The `GoogleLMInvoker` can use either Google Gen AI or Google Vertex AI.

        Google Gen AI is recommended for quick prototyping and development.
        It requires a Gemini API key for authentication.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(
            model_name="gemini-2.5-flash",
            api_key="your_api_key"
        )
        ```

        Google Vertex AI is recommended to build production-ready applications.
        It requires a service account JSON file for authentication.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(
            model_name="gemini-2.5-flash",
            credentials_path="path/to/service_account.json"
        )
        ```

        If neither `api_key` nor `credentials_path` is provided, Google Gen AI will be used by default.
        The `GOOGLE_API_KEY` environment variable will be used for authentication.

    Input types:
        The `GoogleLMInvoker` supports the following input types: text, audio, document, image, and video.
        Non-text inputs can be passed as an `Attachment` object with either the `user` or `assistant` role.

        Usage example:
        ```python
        text = "What animal is in this image?"
        image = Attachment.from_path("path/to/local/image.png")
        result = await lm_invoker.invoke([text, image])
        ```

    Image generation:
        The `GoogleLMInvoker` supports image generation. This can be done by using an image generation model,
        such as `gemini-2.5-flash-image`. Streaming is disabled for image generation models.
        The generated image will be stored in the `attachments` attribute in the output.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker("gemini-2.5-flash-image")
        result = await lm_invoker.invoke("Create a picture...")
        result.attachments[0].write_to_file("path/to/local/image.png")
        ```

        Output example:
        ```python
        LMOutput(
            response="Let me call the tools...",
            attachments=[Attachment(filename="image.png", mime_type="image/png", data=b"...")],
        )
        ```

    Tool calling:
        Tool calling is a feature that allows the language model to call tools to perform tasks.
        Tools can be passed to the via the `tools` parameter as a list of `Tool` objects.
        When tools are provided and the model decides to call a tool, the tool calls are stored in the
        `tool_calls` attribute in the output.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(..., tools=[tool_1, tool_2])
        ```

        Output example:
        ```python
        LMOutput(
            response="Let me call the tools...",
            tool_calls=[
                ToolCall(id="123", name="tool_1", args={"key": "value"}),
                ToolCall(id="456", name="tool_2", args={"key": "value"}),
            ]
        )
        ```

    Structured output:
        Structured output is a feature that allows the language model to output a structured response.
        This feature can be enabled by providing a schema to the `response_schema` parameter.

        The schema must be either a JSON schema dictionary or a Pydantic BaseModel class.
        If JSON schema is used, it must be compatible with Pydantic\'s JSON schema, especially for complex schemas.
        For this reason, it is recommended to create the JSON schema using Pydantic\'s `model_json_schema` method.

        Structured output is not compatible with tool calling. The language model also doesn\'t need to stream
        anything when structured output is enabled. Thus, standard invocation will be performed regardless of
        whether the `event_emitter` parameter is provided or not.

        When enabled, the structured output is stored in the `structured_output` attribute in the output.
        1. If the schema is a JSON schema dictionary, the structured output is a dictionary.
        2. If the schema is a Pydantic BaseModel class, the structured output is a Pydantic model.

        # Example 1: Using a JSON schema dictionary
        Usage example:
        ```python
        schema = {
            "title": "Animal",
            "description": "A description of an animal.",
            "properties": {
                "color": {"title": "Color", "type": "string"},
                "name": {"title": "Name", "type": "string"},
            },
            "required": ["name", "color"],
            "type": "object",
        }
        lm_invoker = GoogleLMInvoker(..., response_schema=schema)
        ```
        Output example:
        ```python
        LMOutput(structured_output={"name": "Golden retriever", "color": "Golden"})
        ```

        # Example 2: Using a Pydantic BaseModel class
        Usage example:
        ```python
        class Animal(BaseModel):
            name: str
            color: str

        lm_invoker = GoogleLMInvoker(..., response_schema=Animal)
        ```
        Output example:
        ```python
        LMOutput(structured_output=Animal(name="Golden retriever", color="Golden"))
        ```

    Analytics tracking:
        Analytics tracking is a feature that allows the module to output additional information about the invocation.
        This feature can be enabled by setting the `output_analytics` parameter to `True`.
        When enabled, the following attributes will be stored in the output:
        1. `token_usage`: The token usage.
        2. `duration`: The duration in seconds.
        3. `finish_details`: The details about how the generation finished.

        Output example:
        ```python
        LMOutput(
            response="Golden retriever is a good dog breed.",
            token_usage=TokenUsage(
                input_tokens=1500,
                output_tokens=200,
                input_token_details=InputTokenDetails(cached_tokens=1200, uncached_tokens=300),
                output_token_details=OutputTokenDetails(reasoning_tokens=180, response_tokens=20),
            ),
            duration=0.729,
            finish_details={"finish_reason": "STOP", "finish_message": None},
        )
        ```

    Retry and timeout:
        The `GoogleLMInvoker` supports retry and timeout configuration.
        By default, the max retries is set to 0 and the timeout is set to 30.0 seconds.
        They can be customized by providing a custom `RetryConfig` object to the `retry_config` parameter.

        Retry config examples:
        ```python
        retry_config = RetryConfig(max_retries=0, timeout=None)  # No retry, no timeout
        retry_config = RetryConfig(max_retries=0, timeout=10.0)  # No retry, 10.0 seconds timeout
        retry_config = RetryConfig(max_retries=5, timeout=None)  # 5 max retries, no timeout
        retry_config = RetryConfig(max_retries=5, timeout=10.0)  # 5 max retries, 10.0 seconds timeout
        ```

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(..., retry_config=retry_config)
        ```

    Thinking:
        Thinking is a feature that allows the language model to have enhanced reasoning capabilities for complex tasks,
        while also providing transparency into its step-by-step thought process before it delivers its final answer.
        It can be enabled by setting the `thinking` parameter to `True`.

        Thinking is only available for certain models, starting from Gemini 2.5 series, and is required for
        Gemini 2.5 Pro models. Therefore, `thinking` defaults to `True` for Gemini 2.5 Pro models and `False`
        for other models. Setting `thinking` to `False` for Gemini 2.5 Pro models will raise a `ValueError`.
        When enabled, the reasoning is stored in the `reasoning` attribute in the output.

        Usage example:
        ```python
        lm_invoker = GoogleLMInvoker(..., thinking=True, thinking_budget=1024)
        ```

        Output example:
        ```python
        LMOutput(
            response="Golden retriever is a good dog breed.",
            reasoning=[Reasoning(reasoning="Let me think about it...")],
        )
        ```

        Streaming output example:
        ```python
        {"type": "thinking_start", "value": "", ...}
        {"type": "thinking", "value": "Let me think "\', ...}
        {"type": "thinking", "value": "about it...", ...}
        {"type": "thinking_end", "value": ""}\', ...}
        {"type": "response", "value": "Golden retriever ", ...}
        {"type": "response", "value": "is a good dog breed.", ...}
        ```
        Note: By default, the thinking token will be streamed with the legacy `EventType.DATA` event type.
        To use the new simplified streamed event format, set the `simplify_events` parameter to `True` during
        LM invoker initialization. The legacy event format support will be removed in v0.6.

        When thinking is enabled, the amount of tokens allocated for the thinking process can be set via the
        `thinking_budget` parameter. The `thinking_budget`:
        1. Defaults to -1, in which case the model will control the budget automatically.
        2. Must be greater than the model\'s minimum thinking budget.
        For more details, please refer to https://ai.google.dev/gemini-api/docs/thinking

    Output types:
        The output of the `GoogleLMInvoker` can either be:
        1. `str`: A text response.
        2. `LMOutput`: A Pydantic model that may contain the following attributes:
            2.1. response (str)
            2.2. attachments (list[Attachment])
            2.3. tool_calls (list[ToolCall])
            2.4. structured_output (dict[str, Any] | BaseModel | None)
            2.5. token_usage (TokenUsage | None)
            2.6. duration (float | None)
            2.7. finish_details (dict[str, Any])
            2.8. reasoning (list[Reasoning])
    '''
    client_params: Incomplete
    generate_image: Incomplete
    thinking: Incomplete
    thinking_budget: Incomplete
    def __init__(self, model_name: str, api_key: str | None = None, credentials_path: str | None = None, project_id: str | None = None, location: str = 'us-central1', model_kwargs: dict[str, Any] | None = None, default_hyperparameters: dict[str, Any] | None = None, tools: list[Tool | LangChainTool] | None = None, response_schema: ResponseSchema | None = None, output_analytics: bool = False, retry_config: RetryConfig | None = None, thinking: bool | None = None, thinking_budget: int = ..., simplify_events: bool = False) -> None:
        '''Initializes a new instance of the GoogleLMInvoker class.

        Args:
            model_name (str): The name of the model to use.
            api_key (str | None, optional): Required for Google Gen AI authentication. Cannot be used together
                with `credentials_path`. Defaults to None.
            credentials_path (str | None, optional): Required for Google Vertex AI authentication. Path to the service
                account credentials JSON file. Cannot be used together with `api_key`. Defaults to None.
            project_id (str | None, optional): The Google Cloud project ID for Vertex AI. Only used when authenticating
                with `credentials_path`. Defaults to None, in which case it will be loaded from the credentials file.
            location (str, optional): The location of the Google Cloud project for Vertex AI. Only used when
                authenticating with `credentials_path`. Defaults to "us-central1".
            model_kwargs (dict[str, Any] | None, optional): Additional keyword arguments for the Google Vertex AI
                client.
            default_hyperparameters (dict[str, Any] | None, optional): Default hyperparameters for invoking the model.
                Defaults to None.
            tools (list[Tool | LangChainTool] | None, optional): Tools provided to the model to enable tool calling.
                Defaults to None.
            response_schema (ResponseSchema | None, optional): The schema of the response. If provided, the model will
                output a structured response as defined by the schema. Supports both Pydantic BaseModel and JSON schema
                dictionary. Defaults to None.
            output_analytics (bool, optional): Whether to output the invocation analytics. Defaults to False.
            retry_config (RetryConfig | None, optional): The retry configuration for the language model.
                Defaults to None, in which case a default config with no retry and 30.0 seconds timeout will be used.
            thinking (bool | None, optional): Whether to enable thinking. Only allowed for thinking models.
                Defaults to True for Gemini 2.5 Pro models and False for other models.
            thinking_budget (int, optional): The tokens allowed for thinking process. Only allowed for thinking models.
                Defaults to -1, in which case the model will control the budget automatically.
            simplify_events (bool, optional): Temporary parameter to control the streamed events format.
                When True, uses the simplified events format. When False, uses the legacy events format for
                backward compatibility. Will be removed in v0.6. Defaults to False.

        Note:
            If neither `api_key` nor `credentials_path` is provided, Google Gen AI will be used by default.
            The `GOOGLE_API_KEY` environment variable will be used for authentication.
        '''
    def set_tools(self, tools: list[Tool | LangChainTool]) -> None:
        """Sets the tools for the Google language model.

        This method sets the tools for the Google language model. Any existing tools will be replaced.

        Args:
            tools (list[Tool | LangChainTool]): The list of tools to be used.

        Raises:
            ValueError: If `response_schema` exists.
        """
    def set_response_schema(self, response_schema: ResponseSchema | None) -> None:
        """Sets the response schema for the Google language model.

        This method sets the response schema for the Google language model. Any existing response schema will be
        replaced.

        Args:
            response_schema (ResponseSchema | None): The response schema to be used.

        Raises:
            ValueError: If `tools` exists.
        """
