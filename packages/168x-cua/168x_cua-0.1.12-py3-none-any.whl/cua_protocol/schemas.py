from datetime import datetime, timezone
from uuid import UUID
import enum

from typing_extensions import Annotated, TypeAlias
from typing import Union, Literal
from pydantic import BaseModel, Field, ConfigDict

# ------------------------------------------------------------
# General
# ------------------------------------------------------------

class LLMPreset(str, enum.Enum):
    ANTHROPIC_SONNET_4_5_MAINAGENT = "anthropic_sonnet_4_5_mainagent"
    ANTHROPIC_SONNET_4_5_SUBAGENT = "anthropic_sonnet_4_5_subagent"

# ------------------------------------------------------------
# Register
# ------------------------------------------------------------

class RegisterRequest(BaseModel):
    agent_instance_id: str
    secret_key: str
    private_ip: str | None
    type: str
    azure_vm_id: str


class RegisterResponse(BaseModel):
    accepted: bool

# ------------------------------------------------------------
# CheckIn Request
# ------------------------------------------------------------

class BaseEvent(BaseModel):
    type: str
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: UUID | None = None

class OutboundMessageEvent(BaseEvent):
    type: Literal["outbound_message"] = "outbound_message"
    
    text: str
    
class ToolCallEvent(BaseEvent):
    type: Literal["tool_call"] = "tool_call"
    
    tool_name: str
    tool_args: str
    tool_call_title: str
    
class ToolResultEvent(BaseEvent):
    type: Literal["tool_result"] = "tool_result"
    
    tool_outcome: Literal["success", "error", "unknown_tool", "interrupted"]
    tool_output_text: str | None
    tool_output_base64_png_list: list[str] | None

Event: TypeAlias = Annotated[
    Union[
        OutboundMessageEvent,
        ToolCallEvent,
        ToolResultEvent,
    ],
   Field(discriminator="type"),
]

class CheckInRequest(BaseModel):
    agent_instance_id: str
    secret_key: str
    last_updated_at: datetime | None
    await_new_message: bool
    await_run: bool
    
    events: list[Event]

class Message(BaseModel):
    id: UUID
    thread_id: UUID
    created_at: datetime
    updated_at: datetime
    
    text: str


# ------------------------------------------------------------
# Check In Response
# ------------------------------------------------------------

class ToolDefinition(BaseModel):
    name: str
    parameters: dict 


class SubagentDefinition(BaseModel):
    name: str
    
    model: LLMPreset
    system_prompt: str
    tools: list[ToolDefinition]


class CheckInResponse(BaseModel):
    # For downward compatibility
    model_config = ConfigDict(extra="ignore")
    
    # agent persona
    model: LLMPreset
    system_prompt: str
    tools: list[ToolDefinition]
    subagents: list[SubagentDefinition]
    
    # legacy subagents
    legacy_subagent_workflows: str | None
    
    # control
    run: bool
    
    # input
    new_messages: list[Message]


# ------------------------------------------------------------
# LLM Request
# ------------------------------------------------------------

class BaseLLMRequest(BaseModel):
    type: LLMPreset
    
    agent_instance_id: UUID
    secret_key: str

class AnthropicSonnet45MainAgentRequest(BaseLLMRequest):
    type: Literal[LLMPreset.ANTHROPIC_SONNET_4_5_MAINAGENT] = LLMPreset.ANTHROPIC_SONNET_4_5_MAINAGENT
    
    messages: list
    system_prompt: str | None
    tools: list[dict] | None
    

class AnthropicSonnet45SubAgentRequest(BaseLLMRequest):
    type: Literal[LLMPreset.ANTHROPIC_SONNET_4_5_SUBAGENT] = LLMPreset.ANTHROPIC_SONNET_4_5_SUBAGENT
    
    messages: list
    system_prompt: str | None
    tools: list[dict] | None


LLMRequest: TypeAlias = Annotated[
    Union[
        AnthropicSonnet45MainAgentRequest,
        AnthropicSonnet45SubAgentRequest,
    ],
   Field(discriminator="type"),
]
# ------------------------------------------------------------
# LLM Response
# ------------------------------------------------------------

class ToolCall(BaseModel):
    call_id: str
    name: str
    input: str

class BaseLLMResponse(BaseModel):
    contents: list
    
    # parsed response
    text: str | None
    thinking_text: str | None
    tool_calls: list[ToolCall] | None
    end_turn: bool