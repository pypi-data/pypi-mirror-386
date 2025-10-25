"""
Chat history middleware for saving conversations to various storage backends.

This module uses LangChain v1 middleware pattern to automatically save
chat messages to the database after each model response.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any

from langchain.agents.middleware import AgentMiddleware, AgentState
from langchain.messages import RemoveMessage
from langchain_core.messages import AnyMessage
from langgraph.runtime import Runtime
from langgraph.typing import ContextT

from .utils.logging import get_graph_logger
from .storage import ChatStorage

logger = get_graph_logger(__name__)
# Disable propagation to avoid duplicate logs (LangGraph handles the logging)
logger._logger.propagate = False

__all__ = ["ChatSaver", "ToolFilter"]


@dataclass
class ContextSchema:
    user_id: str
    thread_id: str
    jwt_token: str


class ToolFilter(AgentMiddleware[AgentState, ContextT]):
    """
    Middleware to filter out tool messages from chat history.

    This middleware removes tool-related messages that shouldn't be saved:
    1. Messages with type 'tool'
    2. AI messages that trigger tool calls (finish_reason == 'tool_calls')

    Usage:
        agent = create_agent(
            model="openai:gpt-4o",
            tools=[...],
            middleware=[
                ToolFilter(),   # Filter before and after (default)
                ChatSaver()     # Then save
            ],
            context_schema=ContextSchema,
        )
    """

    def __init__(self, when: str = "both"):
        """
        Initialize the tool filter middleware.

        Args:
            when: When to filter messages - 'before', 'after', or 'both' (default: 'both')
        """
        super().__init__()
        if when not in ("before", "after", "both"):
            raise ValueError(f"Invalid 'when' value: {when}. Must be 'before', 'after', or 'both'")
        self.when = when

    def _filter_tool_messages(
        self,
        messages: list[AnyMessage],
        stage: str,
    ) -> Dict[str, Any] | None:
        """
        Filter tool messages from the message list using RemoveMessage.

        Args:
            messages: List of messages to filter
            stage: Stage name for logging ('before_agent' or 'after_agent')

        Returns:
            Updated state dict with RemoveMessage instances or None if no filtering occurred
        """
        if not messages:
            return None

        # Collect IDs of messages to remove
        messages_to_remove = []
        for msg in messages:
            # Mark tool messages for removal
            if msg.type == "tool":
                logger.debug(f"[{stage}] Filtering out tool message: {msg.id}")
                messages_to_remove.append(RemoveMessage(id=str(msg.id)))

            # Mark AI messages that trigger tool calls for removal
            elif msg.type == "ai":
                finish_reason = getattr(msg, "response_metadata", {}).get("finish_reason", "")
                if finish_reason == "tool_calls":
                    logger.debug(f"[{stage}] Filtering out AI message with tool_calls: {msg.id}")
                    messages_to_remove.append(RemoveMessage(id=str(msg.id)))

        # Only return update if we have messages to remove
        if messages_to_remove:
            logger.debug(f"[{stage}] Marked {len(messages_to_remove)} tool-related messages for removal")
            return {"messages": messages_to_remove}

        return None

    def before_agent(
        self,
        state: AgentState,
        runtime: Runtime[ContextT],
    ) -> Dict[str, Any] | None:
        """
        Filter tool messages from the state before agent call.

        Args:
            state: Current agent state containing messages
            runtime: Runtime context

        Returns:
            Updated state dict with filtered messages
        """
        if self.when not in ("before", "both"):
            return None

        messages: list[AnyMessage] = state.get("messages", [])
        return self._filter_tool_messages(messages, "before_agent")

    def after_agent(
        self,
        state: AgentState,
        runtime: Runtime[ContextT],
    ) -> Dict[str, Any] | None:
        """
        Filter tool messages from the state after agent call.

        Args:
            state: Current agent state containing messages
            runtime: Runtime context

        Returns:
            Updated state dict with filtered messages
        """
        if self.when not in ("after", "both"):
            return None

        messages: list[AnyMessage] = state.get("messages", [])
        return self._filter_tool_messages(messages, "after_agent")


class ChatSaver(AgentMiddleware[AgentState, ContextT]):
    """
    Middleware to save chat history to various storage backends after each model response.

    This middleware automatically captures and persists conversation history
    to the database, including message content, and metadata.
    Supports multiple storage backends: SQLite (default), Supabase, and Firebase.

    Usage:
        # Using SQLite in-memory (default - easiest to get started)
        agent = create_agent(
            model="openai:gpt-4o",
            tools=[...],
            middleware=[ChatSaver()],
            context_schema=ContextSchema,
        )

        # Using SQLite with file storage
        agent = create_agent(
            model="openai:gpt-4o",
            tools=[...],
            middleware=[ChatSaver(db_path="./chat.db")],
            context_schema=ContextSchema,
        )

        # Using Supabase
        agent = create_agent(
            model="openai:gpt-4o",
            tools=[...],
            middleware=[ChatSaver(
                backend="supabase",
                supabase_url="https://your-project.supabase.co",
                supabase_key="your-anon-key",
            )],
            context_schema=ContextSchema
        )

        # Using Firebase
        agent = create_agent(
            model="openai:gpt-4o",
            tools=[...],
            middleware=[ChatSaver(backend="firebase", credentials_path="/path/to/firebase-creds.json")],
            context_schema=ContextSchema,
        )

        agent.invoke(
            {"messages": [...]},
            context=ContextSchema(user_id="user-123", thread_id="thread-123", jwt_token="...")
        )
    """

    def __init__(
        self,
        save_interval: int = 1,
        extract_interval: int = 5,
        backend: str = "sqlite",
        **backend_kwargs
    ):
        """
        Initialize chat history middleware.

        Args:
            save_interval: Save to database after every N model responses (default: 1)
            backend: Storage backend to use ('sqlite', 'supabase', 'firebase'), default: 'sqlite'
            **backend_kwargs: Backend-specific initialization parameters:
                - For SQLite: db_path (str, default: ":memory:" for in-memory database)
                - For Supabase: supabase_url (str), supabase_key (str), or client (optional Supabase client instance)
                - For Firebase: credentials_path (str, optional)
        """
        super().__init__()
        self.save_interval = save_interval
        self._model_call_count = 0
        self._saved_msg_ids = set()  # Persistent tracking of saved message IDs
        self._logged_messages = set()  # Track all log messages already displayed to avoid duplicates

        # Set default db_path for SQLite if not provided
        if backend == "sqlite" and "db_path" not in backend_kwargs:
            backend_kwargs["db_path"] = ":memory:"

        # Initialize storage backend
        try:
            self.storage = ChatStorage.create(backend, **backend_kwargs)
            logger.info(f"Initialized ChatSaver with {backend} backend")
        except Exception as e:
            logger.error(f"Failed to initialize storage backend '{backend}': {e}")
            raise

    def after_agent(
        self,
        state: AgentState,
        runtime: Runtime[ContextT],
    ) -> Dict[str, Any] | None:
        """
        Save chat history after model responds.

        This hook is called after each model response, allowing us to
        persist the conversation state to the configured storage backend.

        Args:
            state: Current agent state containing messages
            runtime: Runtime context with user_id, thread_id, and jwt_token

        Returns:
            Dict with collected logs or None
        """
        # Increment call count
        self._model_call_count += 1

        # Only save on the configured interval
        if self._model_call_count % self.save_interval != 0:
            return None

        graph_logs = []
        thread_id = getattr(runtime.context, "thread_id", None)
        jwt_token = getattr(runtime.context, "jwt_token", None)
        user_id = getattr(runtime.context, "user_id", None)

        if not thread_id:
            log_msg = "[after_agent] Missing thread_id in context; cannot save chat history."
            if log_msg not in self._logged_messages:
                graph_logs.append(logger.error(log_msg))
                self._logged_messages.add(log_msg)
            return {"logs": graph_logs}

        # Get messages from state
        messages: list[AnyMessage] = state.get("messages", [])

        if not messages:
            if logger.isEnabledFor(logging.DEBUG):
                log_msg = f"[after_agent] No messages to save for thread {thread_id}"
                if log_msg not in self._logged_messages:
                    graph_logs.append(logger.debug(log_msg))
                    self._logged_messages.add(log_msg)
            return {"logs": graph_logs}

        # Prepare credentials based on available context
        credentials = {"user_id": user_id}
        if jwt_token:
            # Add token with appropriate key based on backend type
            backend_type = type(self.storage.backend).__name__.lower()
            if "firebase" in backend_type:
                credentials["id_token"] = jwt_token
            else:  # Supabase or other JWT-based backends
                credentials["jwt_token"] = jwt_token

        # Use the ChatStorage instance to save chat history
        result = self.storage.save_chat_history(
            thread_id=thread_id,
            credentials=credentials,
            messages=messages,
            user_id=user_id,
            saved_msg_ids=self._saved_msg_ids,  # Pass persistent set
        )

        # Update the persistent set with newly saved message IDs
        if "saved_msg_ids" in result:
            self._saved_msg_ids.update(result["saved_msg_ids"])

        # Log the result
        if result["success"]:
            if result["saved_count"] > 0:
                log_msg = (
                    f"[after_agent] Saved {result['saved_count']} messages for thread {thread_id} "
                    f"(skipped {result.get('skipped_count', 0)} already saved)"
                )
                if log_msg not in self._logged_messages:
                    graph_logs.append(logger.info(log_msg))
                    self._logged_messages.add(log_msg)
        else:
            # Only log each unique error once per session
            for error in result["errors"]:
                log_msg = f"[after_agent] Chat history save error: {error}"
                if log_msg not in self._logged_messages:
                    graph_logs.append(logger.error(log_msg))
                    self._logged_messages.add(log_msg)

        return {"logs": graph_logs}
