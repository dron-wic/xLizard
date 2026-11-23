"""xLizard — локальный анализатор метрик сложности C/C++."""

__version__ = "1.1.9"
version = __version__

from xlizard.combined_metrics import CombinedMetrics
from xlizard.sourcemonitor_metrics import Config, SourceMonitorMetrics

__all__ = [
    "__version__",
    "version",
    "CombinedMetrics",
    "Config",
    "SourceMonitorMetrics",
]
