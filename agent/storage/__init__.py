"""Storage interfaces and implementations.

Three storage types:

1. Memory (agent conversation state)
   - Interface: Strands' built-in SessionManager (not ours to define)
   - Local: FileSessionManager (from strands.session.file_session_manager)
   - Production: AgentCoreMemorySessionManager (from bedrock_agentcore)
   - Configured in: session_factory.py → create_session_manager()

2. Chat History (thread metadata for the UI sidebar)
   - Interface: ThreadIndexStorage
   - Local: JsonFileThreadIndex (one JSON file per thread in data/threads/)
   - Production: DynamoDBThreadIndex or S3ThreadIndex (to be implemented)

3. Charts (generated PNG images)
   - Interface: ChartStorage
   - Local: LocalChartStorage (files in data/charts/)
   - Production: S3ChartStorage + CloudFront URL (to be implemented)
"""

from .base import ThreadIndexStorage, ThreadMeta
from .json_file_storage import JsonFileThreadIndex
from .chart_storage import ChartStorage, LocalChartStorage

__all__ = [
    # Chat History
    "ThreadIndexStorage",
    "ThreadMeta",
    "JsonFileThreadIndex",
    # Charts
    "ChartStorage",
    "LocalChartStorage",
]
