# Import key components that should be publicly accessible
from trajectory.clients import client, together_client
from trajectory.judgment_client import JudgmentClient
from trajectory.common.tracer import Tracer, wrap
from trajectory.version_check import check_latest_version

# Preferred public alias
TrajectoryClient = JudgmentClient

check_latest_version()

__all__ = [
    # Clients
    "client",
    "together_client",
    # Tracing
    "Tracer",
    "wrap",
    # Preferred public name
    "TrajectoryClient",
    # Backward-compat
    "JudgmentClient",
]