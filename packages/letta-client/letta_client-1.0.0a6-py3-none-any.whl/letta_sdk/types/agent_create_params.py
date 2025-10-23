# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Union, Iterable, Optional
from typing_extensions import Annotated, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo
from .agent_type import AgentType
from .llm_config_param import LlmConfigParam
from .create_block_param import CreateBlockParam
from .init_tool_rule_param import InitToolRuleParam
from .message_create_param import MessageCreateParam
from .child_tool_rule_param import ChildToolRuleParam
from .embedding_config_param import EmbeddingConfigParam
from .parent_tool_rule_param import ParentToolRuleParam
from .continue_tool_rule_param import ContinueToolRuleParam
from .terminal_tool_rule_param import TerminalToolRuleParam
from .text_response_format_param import TextResponseFormatParam
from .conditional_tool_rule_param import ConditionalToolRuleParam
from .json_object_response_format_param import JsonObjectResponseFormatParam
from .json_schema_response_format_param import JsonSchemaResponseFormatParam
from .requires_approval_tool_rule_param import RequiresApprovalToolRuleParam
from .max_count_per_step_tool_rule_param import MaxCountPerStepToolRuleParam
from .required_before_exit_tool_rule_param import RequiredBeforeExitToolRuleParam

__all__ = ["AgentCreateParams", "ResponseFormat", "ToolRule"]


class AgentCreateParams(TypedDict, total=False):
    agent_type: AgentType
    """The type of agent."""

    base_template_id: Optional[str]
    """The base template id of the agent."""

    block_ids: Optional[SequenceNotStr[str]]
    """The ids of the blocks used by the agent."""

    context_window_limit: Optional[int]
    """The context window limit used by the agent."""

    description: Optional[str]
    """The description of the agent."""

    embedding: Optional[str]
    """
    The embedding configuration handle used by the agent, specified in the format
    provider/model-name.
    """

    embedding_chunk_size: Optional[int]
    """The embedding chunk size used by the agent."""

    embedding_config: Optional[EmbeddingConfigParam]
    """Configuration for embedding model connection and processing parameters."""

    enable_reasoner: Optional[bool]
    """Whether to enable internal extended thinking step for a reasoner model."""

    enable_sleeptime: Optional[bool]
    """If set to True, memory management will move to a background agent thread."""

    from_template: Optional[str]
    """The template id used to configure the agent"""

    hidden: Optional[bool]
    """If set to True, the agent will be hidden."""

    identity_ids: Optional[SequenceNotStr[str]]
    """The ids of the identities associated with this agent."""

    include_base_tool_rules: Optional[bool]
    """If true, attaches the Letta base tool rules (e.g.

    deny all tools not explicitly allowed).
    """

    include_base_tools: bool
    """If true, attaches the Letta core tools (e.g. core_memory related functions)."""

    include_default_source: bool
    """
    If true, automatically creates and attaches a default data source for this
    agent.
    """

    include_multi_agent_tools: bool
    """If true, attaches the Letta multi-agent tools (e.g.

    sending a message to another agent).
    """

    initial_message_sequence: Optional[Iterable[MessageCreateParam]]
    """The initial set of messages to put in the agent's in-context memory."""

    llm_config: Optional[LlmConfigParam]
    """Configuration for Language Model (LLM) connection and generation parameters."""

    max_files_open: Optional[int]
    """Maximum number of files that can be open at once for this agent.

    Setting this too high may exceed the context window, which will break the agent.
    """

    max_reasoning_tokens: Optional[int]
    """The maximum number of tokens to generate for reasoning step.

    If not set, the model will use its default value.
    """

    max_tokens: Optional[int]
    """The maximum number of tokens to generate, including reasoning step.

    If not set, the model will use its default value.
    """

    memory_blocks: Optional[Iterable[CreateBlockParam]]
    """The blocks to create in the agent's in-context memory."""

    memory_variables: Optional[Dict[str, str]]
    """The variables that should be set for the agent."""

    message_buffer_autoclear: bool
    """
    If set to True, the agent will not remember previous messages (though the agent
    will still retain state via core memory blocks and archival/recall memory). Not
    recommended unless you have an advanced use case.
    """

    metadata: Optional[Dict[str, object]]
    """The metadata of the agent."""

    model: Optional[str]
    """
    The LLM configuration handle used by the agent, specified in the format
    provider/model-name, as an alternative to specifying llm_config.
    """

    name: str
    """The name of the agent."""

    per_file_view_window_char_limit: Optional[int]
    """The per-file view window character limit for this agent.

    Setting this too high may exceed the context window, which will break the agent.
    """

    project: Optional[str]
    """
    Deprecated: Project should now be passed via the X-Project header instead of in
    the request body. If using the sdk, this can be done via the new x_project field
    below.
    """

    project_id: Optional[str]
    """The id of the project the agent belongs to."""

    reasoning: Optional[bool]
    """Whether to enable reasoning for this agent."""

    response_format: Optional[ResponseFormat]
    """The response format for the agent."""

    secrets: Optional[Dict[str, str]]
    """The environment variables for tool execution specific to this agent."""

    source_ids: Optional[SequenceNotStr[str]]
    """The ids of the sources used by the agent."""

    system: Optional[str]
    """The system prompt used by the agent."""

    tags: Optional[SequenceNotStr[str]]
    """The tags associated with the agent."""

    template: bool
    """Whether the agent is a template"""

    template_id: Optional[str]
    """The id of the template the agent belongs to."""

    timezone: Optional[str]
    """The timezone of the agent (IANA format)."""

    tool_exec_environment_variables: Optional[Dict[str, str]]
    """Deprecated: use `secrets` field instead."""

    tool_ids: Optional[SequenceNotStr[str]]
    """The ids of the tools used by the agent."""

    tool_rules: Optional[Iterable[ToolRule]]
    """The tool rules governing the agent."""

    tools: Optional[SequenceNotStr[str]]
    """The tools used by the agent."""

    x_project: Annotated[str, PropertyInfo(alias="X-Project")]
    """The project slug to associate with the agent (cloud only)."""


ResponseFormat: TypeAlias = Union[TextResponseFormatParam, JsonSchemaResponseFormatParam, JsonObjectResponseFormatParam]

ToolRule: TypeAlias = Union[
    ChildToolRuleParam,
    InitToolRuleParam,
    TerminalToolRuleParam,
    ConditionalToolRuleParam,
    ContinueToolRuleParam,
    RequiredBeforeExitToolRuleParam,
    MaxCountPerStepToolRuleParam,
    ParentToolRuleParam,
    RequiresApprovalToolRuleParam,
]
