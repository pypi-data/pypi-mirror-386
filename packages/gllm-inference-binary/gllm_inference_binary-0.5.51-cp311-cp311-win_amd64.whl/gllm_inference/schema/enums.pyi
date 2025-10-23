from enum import StrEnum

class AttachmentType(StrEnum):
    """Defines valid attachment types."""
    AUDIO = 'audio'
    DOCUMENT = 'document'
    IMAGE = 'image'
    VIDEO = 'video'

class BatchStatus(StrEnum):
    """Defines the status of a batch job."""
    CANCELING = 'canceling'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'
    UNKNOWN = 'unknown'

class LMEventType(StrEnum):
    """Defines event types to be emitted by the LM invoker."""
    ACTIVITY = 'activity'
    CODE = 'code'
    THINKING = 'thinking'

class LMEventTypeSuffix(StrEnum):
    """Defines suffixes for LM event types."""
    START = '_start'
    END = '_end'

class EmitDataType(StrEnum):
    """Defines valid data types for emitting events."""
    ACTIVITY = 'activity'
    CODE = 'code'
    CODE_START = 'code_start'
    CODE_END = 'code_end'
    THINKING = 'thinking'
    THINKING_START = 'thinking_start'
    THINKING_END = 'thinking_end'

class ActivityType(StrEnum):
    """Defines valid activity types."""
    FIND_IN_PAGE = 'find_in_page'
    MCP_CALL = 'mcp_call'
    MCP_LIST_TOOLS = 'mcp_list_tools'
    OPEN_PAGE = 'open_page'
    SEARCH = 'search'
    WEB_SEARCH = 'web_search'

class MessageRole(StrEnum):
    """Defines valid message roles."""
    SYSTEM = 'system'
    USER = 'user'
    ASSISTANT = 'assistant'

class TruncateSide(StrEnum):
    """Enumeration for truncation sides."""
    RIGHT = 'RIGHT'
    LEFT = 'LEFT'

class JinjaEnvType(StrEnum):
    """Enumeration for Jinja environment types."""
    JINJA_DEFAULT = 'jinja_default'
    RESTRICTED = 'restricted'

class WebSearchKey(StrEnum):
    """Defines valid web search keys."""
    PATTERN = 'pattern'
    QUERY = 'query'
    SOURCES = 'sources'
    TYPE = 'type'
    URL = 'url'
