import os
from typing import Optional

import dagster as dg
from dagster import ConfigurableResource
from pydantic import Field

from .ssh import SSHConnectionResource


def _optional_env(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """Return an optional string from the environment.

    Treat blank strings as unset so callers can clear defaults by exporting an empty value.
    """
    raw_value = os.getenv(var_name)
    if raw_value is None:
        return default

    cleaned = raw_value.strip()
    if not cleaned:
        return None

    return cleaned


class SlurmQueueConfig(dg.ConfigurableResource):
    """Default Slurm job submission parameters.
    These can be overridden per-asset via metadata or function arguments.
    """

    partition: str = Field(
        default="", description="Slurm partition/queue (empty = cluster default)"
    )
    num_nodes: int = Field(default=1, description="Number of nodes")
    time_limit: str = Field(default="00:30:00", description="Job time limit (HH:MM:SS)")
    cpus: int = Field(default=2, description="CPUs per task")
    gpus_per_node: int = Field(default=0, description="GPUs per node")
    mem: Optional[str] = Field(
        default="4096M",
        description="Memory allocation (omit to use partition defaults)",
    )
    mem_per_cpu: Optional[str] = Field(
        default=None,
        description="Memory per CPU (alternative to mem, usually leave empty)",
    )
    qos: Optional[str] = Field(
        default=None, description="Quality of service / service level"
    )
    reservation: Optional[str] = Field(
        default=None, description="Reservation name for scheduled windows"
    )
    account: Optional[str] = Field(
        default=None,
        description="Accounting project/charge code (required on many systems)",
    )


class SlurmResource(ConfigurableResource):
    """Complete Slurm cluster configuration.
    Combines SSH connection, queue defaults, and cluster-specific paths.
    """

    ssh: SSHConnectionResource = Field(description="SSH connection to Slurm cluster")
    queue: SlurmQueueConfig = Field(description="Default queue parameters")
    remote_base: Optional[str] = Field(
        default=None,
        description="Base directory on remote system (default: ~/pipelines/<run_id>)",
    )

    @classmethod
    def from_env_slurm(cls, ssh: SSHConnectionResource) -> "SlurmResource":
        """Create a SlurmResource by populating most fields from environment variables,
        but requires an explicit, pre-configured SSHConnectionResource to be provided.

        Args:
            ssh: A fully configured SSHConnectionResource instance.

        """
        return cls(
            # Use the provided ssh object directly
            ssh=ssh,
            # The rest of the configuration is still loaded from the environment
            queue=SlurmQueueConfig(
                partition=os.getenv("SLURM_PARTITION", "interactive"),
                time_limit=os.getenv("SLURM_TIME", "00:30:00"),
                cpus=int(os.getenv("SLURM_CPUS", "2")),
                mem=_optional_env("SLURM_MEM", "4096M"),
                mem_per_cpu=_optional_env("SLURM_MEM_PER_CPU"),
                num_nodes=int(os.getenv("SLURM_NUM_NODES", "1")),
                gpus_per_node=int(os.getenv("SLURM_GPUS_PER_NODE", "0")),
                qos=_optional_env("SLURM_QOS"),
                reservation=_optional_env("SLURM_RESERVATION"),
                account=_optional_env("SLURM_ACCOUNT"),
            ),
            remote_base=os.getenv("SLURM_REMOTE_BASE", "/home/submitter"),
        )

    @classmethod
    def from_env(cls) -> "SlurmResource":
        """Create from environment variables."""
        return cls(
            ssh=SSHConnectionResource.from_env(prefix="SLURM_SSH"),
            queue=SlurmQueueConfig(
                partition=os.getenv("SLURM_PARTITION", ""),
                time_limit=os.getenv("SLURM_TIME", "00:10:00"),
                cpus=int(os.getenv("SLURM_CPUS", "1")),
                mem=_optional_env("SLURM_MEM", "256M"),
                mem_per_cpu=_optional_env("SLURM_MEM_PER_CPU"),
                num_nodes=int(os.getenv("SLURM_NUM_NODES", "1")),
                gpus_per_node=int(os.getenv("SLURM_GPUS_PER_NODE", "0")),
                qos=_optional_env("SLURM_QOS"),
                reservation=_optional_env("SLURM_RESERVATION"),
                account=_optional_env("SLURM_ACCOUNT"),
            ),
            remote_base=os.getenv("SLURM_REMOTE_BASE", "/home/submitter"),
        )
