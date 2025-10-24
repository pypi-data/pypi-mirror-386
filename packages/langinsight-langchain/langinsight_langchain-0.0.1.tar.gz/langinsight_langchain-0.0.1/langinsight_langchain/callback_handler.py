"""LangInsight callback handler implementation."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from langchain_core.outputs import LLMResult
from langchain_core.callbacks import BaseCallbackHandler
from langinsight_langchain.client.langinsight_client import Client
from langinsight_langchain.client.langinsight_client.api.default import post_traces
from langinsight_langchain.client.langinsight_client.models.post_traces_body import PostTracesBody

logger = logging.getLogger(__name__)


class CallbackHandler(BaseCallbackHandler):
    """LangInsight callback handler for LangChain tracing.
    
    This handler sends traces to the LangInsight API for observability and monitoring.
    
    Args:
        api_key: The API key for authentication
        endpoint: The base URL of the LangInsight API
        user_id: User identifier for the trace
        session_id: Session identifier for the trace
        metadata: Additional metadata to include in traces
    
    Example:
        ```python
        from langchain_anthropic import ChatAnthropic
        from langchain_core.prompts import ChatPromptTemplate
        from langinsight_langchain import CallbackHandler

        handler = CallbackHandler(
            api_key="your-api-key",
            endpoint="https://api.langinsight.io",
            user_id="user-123",
            session_id="session-456"
        )

        model = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            callbacks=[handler]
        )
        ```
    """

    name = "langinsight_callback_handler"

    def __init__(
        self,
        api_key: str,
        endpoint: str,
        user_id: str,
        session_id: str,
        metadata: Optional[Dict[str, str]] = None,
    ):
        """Initialize the LangInsight callback handler."""
        super().__init__()
        self.api_key = api_key
        self.user_id = user_id
        self.session_id = session_id
        self.metadata = metadata or {}
        self.client = Client(base_url=endpoint.rstrip("/"))
        self._run_start_times: Dict[UUID, datetime] = {}

    def on_llm_start(
        self, serialized: Dict[str, Any], prompts: list[str], *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any
    ) -> None:
        """Record the start time of an LLM run."""
        self._run_start_times[run_id] = datetime.now(timezone.utc)

    def on_llm_end(self, response: LLMResult, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        """Handle the end of an LLM run.
        
        Extracts relevant information from the LLM response and sends it to the LangInsight API.
        """
        if not response.generations or not response.generations[0]:
            return

        generation = response.generations[0][0]
        
        # Extract timing information
        ended_at = datetime.now(timezone.utc)
        started_at = self._run_start_times.pop(run_id, ended_at)

        # Extract message content and metadata
        text = generation.text
        message = generation.message if hasattr(generation, "message") else None
        
        if not message:
            return

        # Extract model and token information from the message
        response_metadata = getattr(message, "response_metadata", {})
        usage_metadata = getattr(message, "usage_metadata", {})
        
        model = response_metadata.get("model", "unknown")
        total_tokens = usage_metadata.get("total_tokens", 0) if isinstance(usage_metadata, dict) else 0
        
        # Send trace to LangInsight API
        self._send_trace(
            model=model,
            token=total_tokens,
            content=text,
            started_at=started_at,
            ended_at=ended_at,
        )

    def _send_trace(
        self,
        model: str,
        token: int,
        content: str,
        started_at: datetime,
        ended_at: datetime,
    ) -> None:
        """Send trace data to the LangInsight API.
        
        Args:
            model: Model name
            token: Total token count
            content: Generated content
            started_at: Start time of the LLM run
            ended_at: End time of the LLM run
        """
        try:
            body = PostTracesBody(
                user_id=self.user_id,
                session_id=self.session_id,
                model=model,
                token=float(token),
                content=content,
                started_at=started_at.isoformat(),
                ended_at=ended_at.isoformat(),
            )

            post_traces.sync(
                client=self.client,
                body=body,
                x_api_key=self.api_key,
            )
        except Exception as e:
            logger.exception("Failed to send trace to LangInsight: %s", e)

