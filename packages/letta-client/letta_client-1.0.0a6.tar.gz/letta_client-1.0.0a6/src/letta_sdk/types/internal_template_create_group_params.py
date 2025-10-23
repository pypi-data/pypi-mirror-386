# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Optional
from typing_extensions import Required, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .dynamic_manager_param import DynamicManagerParam
from .sleeptime_manager_param import SleeptimeManagerParam
from .supervisor_manager_param import SupervisorManagerParam
from .round_robin_manager_param import RoundRobinManagerParam
from .voice_sleeptime_manager_param import VoiceSleeptimeManagerParam

__all__ = ["InternalTemplateCreateGroupParams", "ManagerConfig"]


class InternalTemplateCreateGroupParams(TypedDict, total=False):
    agent_ids: Required[SequenceNotStr[str]]

    base_template_id: Required[str]
    """The id of the base template."""

    deployment_id: Required[str]
    """The id of the deployment."""

    description: Required[str]

    template_id: Required[str]
    """The id of the template."""

    hidden: Optional[bool]
    """If set to True, the group will be hidden."""

    manager_config: ManagerConfig

    project_id: Optional[str]
    """The associated project id."""

    shared_block_ids: SequenceNotStr[str]


ManagerConfig: TypeAlias = Union[
    RoundRobinManagerParam,
    SupervisorManagerParam,
    DynamicManagerParam,
    SleeptimeManagerParam,
    VoiceSleeptimeManagerParam,
]
