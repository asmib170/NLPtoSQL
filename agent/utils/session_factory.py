"""Session factory — creates agents with session-aware memory.

Swap session-manager implementations by setting SESSION_BACKEND env var:
  "file"       → FileSessionManager (local dev, stores in data/sessions/)
  "agentcore"  → AgentCoreMemorySessionManager (production on AWS)
"""

from strands import Agent
from strands.session.file_session_manager import FileSessionManager
from strands.agent.conversation_manager.sliding_window_conversation_manager import SlidingWindowConversationManager

from .config import SESSION_BACKEND, SESSIONS_DIR, AGENTCORE_MEMORY_ID, AWS_REGION, CONVERSATION_WINDOW_SIZE
from nlp_sql_agent import model, SYSTEM_PROMPT
from tools import verify_question, generate_sql, execute_sql, summarize_results, generate_chart

# Number of user+agent interaction pairs to keep in the sliding window
# (loaded from config)


def create_session_manager(session_id: str):
    """Create a session manager for the given session_id.

    Args:
        session_id: UUID string identifying the chat session.

    Returns:
        A Strands-compatible session manager (FileSessionManager or
        AgentCoreMemorySessionManager depending on SESSION_BACKEND).

    Raises:
        NotImplementedError: If SESSION_BACKEND is "agentcore" but the
            bedrock-agentcore package is not installed.
    """
    if SESSION_BACKEND == "agentcore":
        # Uncomment when deploying to AgentCore Runtime:
        # from bedrock_agentcore.memory.integrations.strands.config import AgentCoreMemoryConfig
        # from bedrock_agentcore.memory.integrations.strands.session_manager import AgentCoreMemorySessionManager
        # config = AgentCoreMemoryConfig(
        #     memory_id=AGENTCORE_MEMORY_ID,
        #     session_id=session_id,
        #     actor_id="user",
        # )
        # return AgentCoreMemorySessionManager(
        #     agentcore_memory_config=config,
        #     region_name=AWS_REGION,
        # )
        raise NotImplementedError("Set SESSION_BACKEND=file or install bedrock-agentcore package")

    return FileSessionManager(session_id=session_id, storage_dir=SESSIONS_DIR)


def create_session_agent(session_id: str) -> Agent:
    """Create a Strands Agent wired to the given session's memory.

    The agent is configured with the shared model, system prompt, and all
    five tools (verify_question, generate_sql, execute_sql, summarize_results,
    generate_chart).

    Args:
        session_id: UUID string identifying the chat session.

    Returns:
        A fully configured Agent instance with session persistence.
    """
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[verify_question, generate_sql, execute_sql, summarize_results, generate_chart],
        session_manager=create_session_manager(session_id),
        # SlidingWindowConversationManager keeps only the last N user+agent
        # interaction pairs in the conversation context sent to the LLM.
        # This prevents context window overflow on long conversations while
        # preserving tool use/result pairs to avoid invalid message states.
        # The full history is still persisted by the session_manager — this
        # only controls what the LLM sees per invocation.
        conversation_manager=SlidingWindowConversationManager(window_size=CONVERSATION_WINDOW_SIZE),
    )
