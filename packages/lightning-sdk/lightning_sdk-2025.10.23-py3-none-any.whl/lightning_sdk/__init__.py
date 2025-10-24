from lightning_sdk.agents import Agent
from lightning_sdk.ai_hub import AIHub
from lightning_sdk.constants import __GLOBAL_LIGHTNING_UNIQUE_IDS_STORE__  # noqa: F401
from lightning_sdk.deployment import Deployment
from lightning_sdk.helpers import VersionChecker, _set_tqdm_envvars_noninteractive
from lightning_sdk.job import Job
from lightning_sdk.machine import CloudProvider, Machine
from lightning_sdk.mmt import MMT
from lightning_sdk.organization import Organization
from lightning_sdk.plugin import JobsPlugin, MultiMachineTrainingPlugin, Plugin, SlurmJobsPlugin
from lightning_sdk.status import Status
from lightning_sdk.studio import VM, Studio
from lightning_sdk.teamspace import ConnectionType, FolderLocation, Teamspace
from lightning_sdk.user import User

__all__ = [
    "AIHub",
    "Agent",
    "CloudProvider",
    "ConnectionType",
    "Deployment",
    "FolderLocation",
    "Job",
    "JobsPlugin",
    "Machine",
    "MMT",
    "MultiMachineTrainingPlugin",
    "Organization",
    "Plugin",
    "SlurmJobsPlugin",
    "Status",
    "Studio",
    "Teamspace",
    "User",
    "VM",
]

__version__ = "2025.10.23"

_version_checker = VersionChecker()
_version_checker.check_and_prompt_upgrade(__version__)

_set_tqdm_envvars_noninteractive()
