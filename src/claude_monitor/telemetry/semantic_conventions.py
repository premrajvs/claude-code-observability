"""
OpenTelemetry Semantic Conventions for LLM Observability.

This module defines standard attribute names following:
1. OpenTelemetry Semantic Conventions
2. OpenInference Semantic Conventions for LLMs
3. Custom conventions for Claude Code specific data

References:
- https://opentelemetry.io/docs/specs/semconv/
- https://github.com/Arize-ai/openinference

Benefits of following conventions:
- Consistent data model across systems
- Interoperability with observability tools
- Standard dashboards and queries work out of the box
- Better correlation across services
"""

from typing import Final


# ===== Service Identification (OpenTelemetry Standard) =====
SERVICE_NAME: Final[str] = "service.name"
SERVICE_VERSION: Final[str] = "service.version"
SERVICE_INSTANCE_ID: Final[str] = "service.instance.id"
DEPLOYMENT_ENVIRONMENT: Final[str] = "deployment.environment"

# ===== Session Attributes (Custom for Claude Code) =====
SESSION_ID: Final[str] = "session.id"
SESSION_PROJECT_PATH: Final[str] = "session.project_path"
SESSION_SLUG: Final[str] = "session.slug"
SESSION_GIT_BRANCH: Final[str] = "session.git_branch"
SESSION_TOTAL_MESSAGES: Final[str] = "session.total_messages"
SESSION_TOTAL_TOKENS: Final[str] = "session.total_tokens"
SESSION_TOTAL_COST: Final[str] = "session.total_cost"
SESSION_DURATION_SECONDS: Final[str] = "session.duration_seconds"

# ===== Message Attributes =====
MESSAGE_ID: Final[str] = "message.id"
MESSAGE_TYPE: Final[str] = "message.type"  # user, assistant, system, tool_use, tool_result
MESSAGE_ROLE: Final[str] = "message.role"  # user, assistant
MESSAGE_CONTENT_PREVIEW: Final[str] = "message.content.preview"
MESSAGE_CONTENT_LENGTH: Final[str] = "message.content.length"

# ===== LLM Attributes (OpenInference Convention) =====
# Following: https://github.com/Arize-ai/openinference/blob/main/spec/semantic_conventions.md

# Model
LLM_MODEL_NAME: Final[str] = "gen_ai.request.model"  # OTel standard
LLM_MODEL_NAME_ALT: Final[str] = "llm.model_name"  # OpenInference
MODEL_PROVIDER: Final[str] = "gen_ai.system"  # "anthropic"

# Request
LLM_REQUEST_ID: Final[str] = "gen_ai.request.id"
LLM_REQUEST_TEMPERATURE: Final[str] = "gen_ai.request.temperature"
LLM_REQUEST_MAX_TOKENS: Final[str] = "gen_ai.request.max_tokens"
LLM_REQUEST_TOP_P: Final[str] = "gen_ai.request.top_p"

# Response
LLM_RESPONSE_ID: Final[str] = "gen_ai.response.id"
LLM_RESPONSE_FINISH_REASON: Final[str] = "gen_ai.response.finish_reasons"
LLM_RESPONSE_STOP_REASON: Final[str] = "llm.stop_reason"

# ===== Token Usage (OpenInference Convention) =====
TOKEN_COUNT_TOTAL: Final[str] = "llm.token_count.total"
TOKEN_COUNT_PROMPT: Final[str] = "llm.token_count.prompt"  # input
TOKEN_COUNT_COMPLETION: Final[str] = "llm.token_count.completion"  # output

# Custom token types for Claude (cache)
TOKENS_INPUT: Final[str] = "tokens.input"
TOKENS_OUTPUT: Final[str] = "tokens.output"
TOKENS_CACHE_CREATION: Final[str] = "tokens.cache_creation"
TOKENS_CACHE_READ: Final[str] = "tokens.cache_read"
TOKENS_TOTAL: Final[str] = "tokens.total"

# ===== Cost Tracking =====
COST_USD: Final[str] = "cost.usd"
COST_CURRENCY: Final[str] = "cost.currency"  # "USD"

# ===== Tool Usage (Custom) =====
TOOL_NAME: Final[str] = "tool.name"
TOOL_INPUT: Final[str] = "tool.input"
TOOL_RESULT: Final[str] = "tool.result"
TOOL_ERROR: Final[str] = "tool.error"
TOOL_DURATION_MS: Final[str] = "tool.duration_ms"

# ===== Project Context =====
PROJECT_PATH: Final[str] = "project.path"
PROJECT_NAME: Final[str] = "project.name"
GIT_BRANCH: Final[str] = "git.branch"
GIT_COMMIT: Final[str] = "git.commit"

# ===== Span Names (Convention) =====
SPAN_NAME_SESSION: Final[str] = "llm.session"
SPAN_NAME_USER_MESSAGE: Final[str] = "llm.user.message"
SPAN_NAME_ASSISTANT_RESPONSE: Final[str] = "llm.assistant.response"
SPAN_NAME_TOOL_USE: Final[str] = "llm.tool.{tool_name}"
SPAN_NAME_TOOL_RESULT: Final[str] = "llm.tool.result"

# ===== Span Event Names =====
EVENT_MESSAGE_CONTENT: Final[str] = "message.content"
EVENT_TOOL_INPUT: Final[str] = "tool.input"
EVENT_TOOL_RESULT: Final[str] = "tool.result"
EVENT_ERROR: Final[str] = "error"

# ===== Error Attributes (OpenTelemetry Standard) =====
ERROR_TYPE: Final[str] = "error.type"
ERROR_MESSAGE: Final[str] = "error.message"
ERROR_STACK: Final[str] = "error.stack"
EXCEPTION_TYPE: Final[str] = "exception.type"
EXCEPTION_MESSAGE: Final[str] = "exception.message"
EXCEPTION_STACKTRACE: Final[str] = "exception.stacktrace"

# ===== HTTP Attributes (for API calls) =====
HTTP_METHOD: Final[str] = "http.method"
HTTP_URL: Final[str] = "http.url"
HTTP_STATUS_CODE: Final[str] = "http.status_code"
HTTP_REQUEST_CONTENT_LENGTH: Final[str] = "http.request.content_length"
HTTP_RESPONSE_CONTENT_LENGTH: Final[str] = "http.response.content_length"


# ===== Helper Functions =====

def get_span_name_for_tool(tool_name: str) -> str:
    """
    Get standardized span name for a tool.

    Args:
        tool_name: Tool name (e.g., "Read", "Write", "Bash")

    Returns:
        Standardized span name (e.g., "tool.Read")
    """
    return f"tool.{tool_name}"


def get_span_name_for_message_type(message_type: str) -> str:
    """
    Get standardized span name for a message type.

    Args:
        message_type: Message type (user, assistant, tool_use, etc.)

    Returns:
        Standardized span name
    """
    if message_type == "user":
        return SPAN_NAME_USER_MESSAGE
    elif message_type == "assistant":
        return SPAN_NAME_ASSISTANT_RESPONSE
    elif message_type == "tool_use":
        return "tool.use"
    elif message_type == "tool_result":
        return SPAN_NAME_TOOL_RESULT
    else:
        return f"message.{message_type}"


# ===== Attribute Groups for Easy Application =====

def get_session_attributes(
    session_id: str,
    project_path: str = "",
    session_slug: str = "",
    git_branch: str = "",
) -> dict:
    """
    Get standard session attributes.

    Args:
        session_id: Session ID
        project_path: Project path
        session_slug: Session slug
        git_branch: Git branch

    Returns:
        Dictionary of session attributes
    """
    attrs = {
        SESSION_ID: session_id,
    }

    if project_path:
        attrs[SESSION_PROJECT_PATH] = project_path
    if session_slug:
        attrs[SESSION_SLUG] = session_slug
    if git_branch:
        attrs[SESSION_GIT_BRANCH] = git_branch

    return attrs


def get_token_attributes(
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_creation_tokens: int = 0,
    cache_read_tokens: int = 0,
) -> dict:
    """
    Get standard token usage attributes.

    Args:
        input_tokens: Input token count
        output_tokens: Output token count
        cache_creation_tokens: Cache creation token count
        cache_read_tokens: Cache read token count

    Returns:
        Dictionary of token attributes
    """
    attrs = {}

    if input_tokens > 0:
        attrs[TOKENS_INPUT] = input_tokens
        attrs[TOKEN_COUNT_PROMPT] = input_tokens  # OpenInference

    if output_tokens > 0:
        attrs[TOKENS_OUTPUT] = output_tokens
        attrs[TOKEN_COUNT_COMPLETION] = output_tokens  # OpenInference

    if cache_creation_tokens > 0:
        attrs[TOKENS_CACHE_CREATION] = cache_creation_tokens

    if cache_read_tokens > 0:
        attrs[TOKENS_CACHE_READ] = cache_read_tokens

    total = (
        input_tokens
        + output_tokens
        + cache_creation_tokens
        + cache_read_tokens
    )
    if total > 0:
        attrs[TOKENS_TOTAL] = total
        attrs[TOKEN_COUNT_TOTAL] = total  # OpenInference

    return attrs


def get_model_attributes(model_name: str) -> dict:
    """
    Get standard model attributes.

    Args:
        model_name: Model name

    Returns:
        Dictionary of model attributes
    """
    return {
        LLM_MODEL_NAME: model_name,
        LLM_MODEL_NAME_ALT: model_name,  # Duplicate for compatibility
        MODEL_PROVIDER: "anthropic",
    }
