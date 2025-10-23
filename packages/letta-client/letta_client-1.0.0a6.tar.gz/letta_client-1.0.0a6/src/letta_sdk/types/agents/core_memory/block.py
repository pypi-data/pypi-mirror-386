# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Dict, Optional

from ...._models import BaseModel

__all__ = ["Block"]


class Block(BaseModel):
    value: str
    """Value of the block."""

    id: Optional[str] = None
    """The human-friendly ID of the Block"""

    base_template_id: Optional[str] = None
    """The base template id of the block."""

    created_by_id: Optional[str] = None
    """The id of the user that made this Block."""

    deployment_id: Optional[str] = None
    """The id of the deployment."""

    description: Optional[str] = None
    """Description of the block."""

    entity_id: Optional[str] = None
    """The id of the entity within the template."""

    hidden: Optional[bool] = None
    """If set to True, the block will be hidden."""

    is_template: Optional[bool] = None
    """Whether the block is a template (e.g. saved human/persona options)."""

    label: Optional[str] = None
    """Label of the block (e.g. 'human', 'persona') in the context window."""

    last_updated_by_id: Optional[str] = None
    """The id of the user that last updated this Block."""

    limit: Optional[int] = None
    """Character limit of the block."""

    metadata: Optional[Dict[str, object]] = None
    """Metadata of the block."""

    name: Optional[str] = None
    """The id of the template."""

    preserve_on_migration: Optional[bool] = None
    """Preserve the block on template migration."""

    project_id: Optional[str] = None
    """The associated project id."""

    read_only: Optional[bool] = None
    """Whether the agent has read-only access to the block."""
