# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Dict, Optional
from typing_extensions import Required, TypedDict

__all__ = ["BlockUpdateParams"]


class BlockUpdateParams(TypedDict, total=False):
    agent_id: Required[str]
    """The ID of the agent in the format 'agent-<uuid4>'"""

    base_template_id: Optional[str]
    """The base template id of the block."""

    deployment_id: Optional[str]
    """The id of the deployment."""

    description: Optional[str]
    """Description of the block."""

    entity_id: Optional[str]
    """The id of the entity within the template."""

    hidden: Optional[bool]
    """If set to True, the block will be hidden."""

    is_template: bool
    """Whether the block is a template (e.g. saved human/persona options)."""

    label: Optional[str]
    """Label of the block (e.g. 'human', 'persona') in the context window."""

    limit: Optional[int]
    """Character limit of the block."""

    metadata: Optional[Dict[str, object]]
    """Metadata of the block."""

    name: Optional[str]
    """The id of the template."""

    preserve_on_migration: Optional[bool]
    """Preserve the block on template migration."""

    project_id: Optional[str]
    """The associated project id."""

    read_only: bool
    """Whether the agent has read-only access to the block."""

    value: Optional[str]
    """Value of the block."""
