"""Agent component implementation for AGNT5 SDK.

Provides simple agent with external LLM integration and tool orchestration.
Future: Platform-backed agents with durable execution and multi-agent coordination.
"""

from __future__ import annotations

import functools
import json
import logging
from typing import Any, Callable, Dict, List, Optional

from .context import Context
from . import lm
from .lm import GenerateRequest, GenerateResponse, LanguageModel, Message, ModelConfig, ToolDefinition
from .tool import Tool, ToolRegistry
from ._telemetry import setup_module_logger

logger = setup_module_logger(__name__)

# Global agent registry
_AGENT_REGISTRY: Dict[str, "Agent"] = {}


class AgentContext(Context):
    """
    Context for agent execution with conversation state management.

    Extends base Context with:
    - State management via EntityStateManager
    - Conversation history persistence
    - Context inheritance (child agents share parent's state)

    Three initialization modes:
    1. Standalone: Creates own state manager (playground testing)
    2. Inherit WorkflowContext: Shares parent's state manager
    3. Inherit parent AgentContext: Shares parent's state manager

    Example:
        ```python
        # Standalone agent with conversation history
        ctx = AgentContext(run_id="session-1", agent_name="tutor")
        result = await agent.run("Hello", context=ctx)
        result = await agent.run("Continue", context=ctx)  # Remembers previous message

        # Agent in workflow - shares workflow state
        @workflow
        async def research_workflow(ctx: WorkflowContext):
            agent_result = await research_agent.run("Find AI trends", context=ctx)
            # Agent has access to workflow state via inherited context
        ```
    """

    def __init__(
        self,
        run_id: str,
        agent_name: str,
        session_id: Optional[str] = None,
        state_manager: Optional[Any] = None,
        parent_context: Optional[Context] = None,
        attempt: int = 0,
        runtime_context: Optional[Any] = None,
    ):
        """
        Initialize agent context.

        Args:
            run_id: Unique execution identifier
            agent_name: Name of the agent
            session_id: Session identifier for conversation history (default: run_id)
            state_manager: Optional state manager (for context inheritance)
            parent_context: Parent context to inherit state from
            attempt: Retry attempt number
            runtime_context: RuntimeContext for trace correlation
        """
        super().__init__(run_id, attempt, runtime_context)

        self._agent_name = agent_name
        self._session_id = session_id or run_id

        # Determine state adapter based on parent context
        from .entity import EntityStateAdapter, _get_state_adapter

        if state_manager:
            # Explicit state adapter provided (parameter name kept for backward compat)
            self._state_adapter = state_manager
            logger.debug(f"AgentContext using provided state adapter")
        elif parent_context:
            # Try to inherit state adapter from parent
            try:
                # Check if parent is WorkflowContext or AgentContext
                if hasattr(parent_context, '_workflow_entity'):
                    # WorkflowContext - get state adapter from worker context
                    self._state_adapter = _get_state_adapter()
                    logger.debug(f"AgentContext inheriting state from WorkflowContext")
                elif hasattr(parent_context, '_state_adapter'):
                    # Parent AgentContext - share state adapter
                    self._state_adapter = parent_context._state_adapter
                    logger.debug(f"AgentContext inheriting state from parent AgentContext")
                elif hasattr(parent_context, '_state_manager'):
                    # Backward compatibility: parent has old _state_manager
                    self._state_adapter = parent_context._state_manager
                    logger.debug(f"AgentContext inheriting state from parent (legacy)")
                else:
                    # FunctionContext or base Context - create new state adapter
                    self._state_adapter = EntityStateAdapter()
                    logger.debug(f"AgentContext created new state adapter (parent has no state)")
            except RuntimeError as e:
                # _get_state_adapter() failed (not in worker context) - create standalone
                self._state_adapter = EntityStateAdapter()
                logger.debug(f"AgentContext created standalone state adapter (not in worker context)")
        else:
            # Try to get from worker context first
            try:
                self._state_adapter = _get_state_adapter()
                logger.debug(f"AgentContext got state adapter from worker context")
            except RuntimeError as e:
                # Standalone - create new state adapter
                self._state_adapter = EntityStateAdapter()
                logger.debug(f"AgentContext created standalone state adapter")

        # Conversation key for state storage (used for in-memory state)
        self._conversation_key = f"agent:{agent_name}:{self._session_id}:messages"
        # Entity key for database persistence (without :messages suffix to match API expectations)
        self._entity_key = f"agent:{agent_name}:{self._session_id}"
        logger.debug(f"AgentContext initialized - session_id={self._session_id}")

    @property
    def state(self):
        """
        Get state interface for agent state management.

        Note: This is a simplified in-memory state interface for agent-specific data.
        Conversation history is managed separately via get_conversation_history() and
        save_conversation_history() which use the Rust-backed persistence layer.

        Returns:
            Dict-like object for state operations

        Example:
            # Store agent-specific data (in-memory only)
            ctx.state["research_results"] = data
            ctx.state["iteration_count"] = 5
        """
        # Simple dict-based state for agent-specific data
        # This is in-memory only and not persisted to platform
        if not hasattr(self, '_agent_state'):
            self._agent_state = {}
        return self._agent_state

    @property
    def session_id(self) -> str:
        """Get session identifier for this agent context."""
        return self._session_id

    async def get_conversation_history(self) -> List[Message]:
        """
        Retrieve conversation history from state, loading from database if needed.

        Uses the EntityStateAdapter which delegates to Rust core for cache-first loading.

        Returns:
            List of Message objects from conversation history
        """
        entity_type = "AgentSession"
        entity_key = self._entity_key

        # Load session data via adapter (Rust handles cache + platform load)
        session_data = await self._state_adapter.load_state(entity_type, entity_key)

        # Extract messages from session object
        if isinstance(session_data, dict) and "messages" in session_data:
            # New format with session metadata
            messages_data = session_data["messages"]
            logger.debug(f"Loaded {len(messages_data)} messages from session {entity_key}")
        elif isinstance(session_data, list):
            # Old format - just messages array
            messages_data = session_data
            logger.debug(f"Loaded {len(messages_data)} messages (legacy format)")
        else:
            # No messages found
            messages_data = []
            logger.debug(f"No conversation history found for {entity_key}")

        # Convert dict representations back to Message objects
        messages = []
        for msg_dict in messages_data:
            if isinstance(msg_dict, dict):
                role = msg_dict.get("role", "user")
                content = msg_dict.get("content", "")
                if role == "user":
                    messages.append(Message.user(content))
                elif role == "assistant":
                    messages.append(Message.assistant(content))
                else:
                    # Generic message - create with MessageRole enum
                    from .lm import MessageRole
                    msg_role = MessageRole(role) if role in ("user", "assistant", "system") else MessageRole.USER
                    msg = Message(role=msg_role, content=content)
                    messages.append(msg)
            else:
                # Already a Message object
                messages.append(msg_dict)

        return messages

    async def save_conversation_history(self, messages: List[Message]) -> None:
        """
        Save conversation history to state and persist to database.

        Uses the EntityStateAdapter which delegates to Rust core for version-checked saves.

        Args:
            messages: List of Message objects to persist
        """
        logger.debug(f"Saving {len(messages)} messages to conversation history")

        # Convert Message objects to dict for JSON serialization
        messages_data = []
        for msg in messages:
            messages_data.append({
                "role": msg.role.value if hasattr(msg.role, 'value') else str(msg.role),
                "content": msg.content
            })

        import time
        entity_type = "AgentSession"
        entity_key = self._entity_key

        # Load current state with version for optimistic locking
        current_state, current_version = await self._state_adapter.load_with_version(
            entity_type, entity_key
        )

        # Build session object with metadata
        now = time.time()

        # Get custom metadata from instance variable or preserve from loaded state
        custom_metadata = getattr(self, '_custom_metadata', current_state.get("metadata", {}))

        session_data = {
            "session_id": self._session_id,
            "agent_name": self._agent_name,
            "created_at": current_state.get("created_at", now),  # Preserve existing or set new
            "last_message_time": now,
            "message_count": len(messages_data),
            "messages": messages_data,
            "metadata": custom_metadata  # Save custom metadata
        }

        # Save to platform via adapter (Rust handles optimistic locking)
        try:
            new_version = await self._state_adapter.save_state(
                entity_type,
                entity_key,
                session_data,
                current_version
            )
            logger.info(
                f"Persisted conversation history: {entity_key} (version {current_version} -> {new_version})"
            )
        except Exception as e:
            logger.error(f"Failed to persist conversation history to database: {e}")
            # Don't fail - conversation is still in memory for this execution

    async def get_metadata(self) -> Dict[str, Any]:
        """
        Get conversation session metadata.

        Returns session metadata including:
        - created_at: Timestamp of first message (float, Unix timestamp)
        - last_activity: Timestamp of last message (float, Unix timestamp)
        - message_count: Number of messages in conversation (int)
        - custom: Dict of user-provided custom metadata

        Returns:
            Dictionary with metadata. If no conversation exists yet, returns defaults.

        Example:
            ```python
            metadata = await context.get_metadata()
            print(f"Session created: {metadata['created_at']}")
            print(f"User ID: {metadata['custom'].get('user_id')}")
            ```
        """
        entity_type = "AgentSession"
        entity_key = self._entity_key

        # Load session data
        session_data = await self._state_adapter.load_state(entity_type, entity_key)

        if not session_data:
            # No conversation exists yet - return defaults
            return {
                "created_at": None,
                "last_activity": None,
                "message_count": 0,
                "custom": getattr(self, '_custom_metadata', {})
            }

        messages = session_data.get("messages", [])

        # Derive timestamps from messages if available
        created_at = session_data.get("created_at")
        last_activity = session_data.get("last_message_time")

        return {
            "created_at": created_at,
            "last_activity": last_activity,
            "message_count": len(messages),
            "custom": session_data.get("metadata", {})
        }

    def update_metadata(self, **kwargs) -> None:
        """
        Update custom session metadata.

        Metadata will be persisted alongside conversation history on next save.
        Use this to store application-specific data like user_id, preferences, etc.

        Args:
            **kwargs: Key-value pairs to store as metadata

        Example:
            ```python
            # Store user identification and preferences
            context.update_metadata(
                user_id="user-123",
                subscription_tier="premium",
                preferences={"theme": "dark", "language": "en"}
            )

            # Later retrieve it
            metadata = await context.get_metadata()
            user_id = metadata["custom"]["user_id"]
            ```

        Note:
            - Metadata is merged with existing metadata (doesn't replace)
            - Changes persist on next save_conversation_history() call
            - Use simple JSON-serializable types (str, int, float, dict, list)
        """
        if not hasattr(self, '_custom_metadata'):
            self._custom_metadata = {}
        self._custom_metadata.update(kwargs)


class Handoff:
    """Configuration for agent-to-agent handoff.

    Handoffs enable one agent to delegate control to another specialized agent,
    following the pattern popularized by LangGraph and OpenAI Agents SDK.

    The handoff is exposed to the LLM as a tool named 'transfer_to_{agent_name}'
    that allows explicit delegation with conversation history.

    Example:
        ```python
        specialist = Agent(name="specialist", ...)

        # Create handoff configuration
        handoff_to_specialist = Handoff(
            agent=specialist,
            description="Transfer to specialist for detailed analysis"
        )

        # Use in coordinator agent
        coordinator = Agent(
            name="coordinator",
            handoffs=[handoff_to_specialist]
        )
        ```
    """

    def __init__(
        self,
        agent: "Agent",
        description: Optional[str] = None,
        tool_name: Optional[str] = None,
        pass_full_history: bool = True,
    ):
        """Initialize handoff configuration.

        Args:
            agent: Target agent to hand off to
            description: Description shown to LLM (defaults to agent instructions)
            tool_name: Custom tool name (defaults to 'transfer_to_{agent_name}')
            pass_full_history: Whether to pass full conversation history to target agent
        """
        self.agent = agent
        self.description = description or agent.instructions or f"Transfer to {agent.name}"
        self.tool_name = tool_name or f"transfer_to_{agent.name}"
        self.pass_full_history = pass_full_history


def handoff(
    agent: "Agent",
    description: Optional[str] = None,
    tool_name: Optional[str] = None,
    pass_full_history: bool = True,
) -> Handoff:
    """Create a handoff configuration for agent-to-agent delegation.

    This is a convenience function for creating Handoff instances with a clean API.

    Args:
        agent: Target agent to hand off to
        description: Description shown to LLM
        tool_name: Custom tool name
        pass_full_history: Whether to pass full conversation history

    Returns:
        Handoff configuration

    Example:
        ```python
        from agnt5 import Agent, handoff

        research_agent = Agent(name="researcher", ...)
        writer_agent = Agent(name="writer", ...)

        coordinator = Agent(
            name="coordinator",
            handoffs=[
                handoff(research_agent, "Transfer for research tasks"),
                handoff(writer_agent, "Transfer for writing tasks"),
            ]
        )
        ```
    """
    return Handoff(
        agent=agent,
        description=description,
        tool_name=tool_name,
        pass_full_history=pass_full_history,
    )


class AgentRegistry:
    """Registry for agents."""

    @staticmethod
    def register(agent: "Agent") -> None:
        """Register an agent."""
        if agent.name in _AGENT_REGISTRY:
            logger.warning(f"Overwriting existing agent '{agent.name}'")
        _AGENT_REGISTRY[agent.name] = agent
        logger.debug(f"Registered agent '{agent.name}'")

    @staticmethod
    def get(name: str) -> Optional["Agent"]:
        """Get agent by name."""
        return _AGENT_REGISTRY.get(name)

    @staticmethod
    def all() -> Dict[str, "Agent"]:
        """Get all registered agents."""
        return _AGENT_REGISTRY.copy()

    @staticmethod
    def clear() -> None:
        """Clear all registered agents."""
        _AGENT_REGISTRY.clear()
        logger.debug("Cleared agent registry")


class AgentResult:
    """Result from agent execution."""

    def __init__(
        self,
        output: str,
        tool_calls: List[Dict[str, Any]],
        context: Context,
        handoff_to: Optional[str] = None,
        handoff_metadata: Optional[Dict[str, Any]] = None,
    ):
        self.output = output
        self.tool_calls = tool_calls
        self.context = context
        self.handoff_to = handoff_to  # Name of agent that was handed off to
        self.handoff_metadata = handoff_metadata or {}  # Additional handoff info


class Agent:
    """Autonomous LLM-driven agent with tool orchestration.

    Current features:
    - LLM integration (OpenAI, Anthropic, etc.)
    - Tool selection and execution
    - Multi-turn reasoning
    - Context and state management

    Future enhancements:
    - Durable execution with checkpointing
    - Multi-agent coordination
    - Platform-backed tool execution
    - Streaming responses

    Example:
        ```python
        from agnt5 import Agent, tool, Context

        @tool(auto_schema=True)
        async def search_web(ctx: Context, query: str) -> List[Dict]:
            # Search implementation
            return [{"title": "Result", "url": "..."}]

        # Simple usage with model string
        agent = Agent(
            name="researcher",
            model="openai/gpt-4o-mini",
            instructions="You are a research assistant.",
            tools=[search_web],
            temperature=0.7
        )

        result = await agent.run("What are the latest AI trends?")
        print(result.output)
        ```
    """

    def __init__(
        self,
        name: str,
        model: Any,  # Can be string like "openai/gpt-4o-mini" OR LanguageModel instance
        instructions: str,
        tools: Optional[List[Any]] = None,
        handoffs: Optional[List[Handoff]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        top_p: Optional[float] = None,
        model_config: Optional[ModelConfig] = None,
        max_iterations: int = 10,
        model_name: Optional[str] = None,  # For backwards compatibility with tests
    ):
        """Initialize agent.

        Args:
            name: Agent name/identifier
            model: Model string with provider prefix (e.g., "openai/gpt-4o-mini") OR LanguageModel instance
            instructions: System instructions for the agent
            tools: List of tools available to the agent (functions, Tool instances, or Agent instances)
            handoffs: List of Handoff configurations for agent-to-agent delegation
            temperature: LLM temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            model_config: Optional advanced configuration (custom endpoints, headers, etc.)
            max_iterations: Maximum reasoning iterations
            model_name: Optional model name (for backwards compatibility, used when model is a LanguageModel instance)
        """
        self.name = name
        self.instructions = instructions
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.model_config = model_config
        self.max_iterations = max_iterations

        # Support both string model names and LanguageModel instances
        if isinstance(model, str):
            # New API: model is a string like "openai/gpt-4o-mini"
            self.model = model
            self.model_name = model_name or model
            self._language_model = None  # Will create on demand
        elif isinstance(model, LanguageModel):
            # Old API (for tests): model is a LanguageModel instance
            self._language_model = model
            self.model = model  # Keep for backwards compatibility
            self.model_name = model_name or "mock-model"
        else:
            raise TypeError(f"model must be a string or LanguageModel instance, got {type(model)}")

        # Store handoffs for building handoff tools
        self.handoffs = handoffs or []

        # Build tool registry (includes regular tools, agent-as-tools, and handoff tools)
        self.tools: Dict[str, Tool] = {}
        if tools:
            for tool_item in tools:
                # Check if it's an Agent instance (agents-as-tools pattern)
                if isinstance(tool_item, Agent):
                    agent_tool = tool_item.to_tool()
                    self.tools[agent_tool.name] = agent_tool
                    logger.info(f"Added agent '{tool_item.name}' as tool to '{self.name}'")
                # Check if it's a Tool instance
                elif isinstance(tool_item, Tool):
                    self.tools[tool_item.name] = tool_item
                # Check if it's a decorated function with config
                elif hasattr(tool_item, "_agnt5_config"):
                    # Try to get from ToolRegistry first
                    tool_config = tool_item._agnt5_config
                    tool_instance = ToolRegistry.get(tool_config.name)
                    if tool_instance:
                        self.tools[tool_instance.name] = tool_instance
                # Otherwise try to look up by function name
                elif callable(tool_item):
                    # Try to find in registry by function name
                    tool_name = tool_item.__name__
                    tool_instance = ToolRegistry.get(tool_name)
                    if tool_instance:
                        self.tools[tool_instance.name] = tool_instance

        # Build handoff tools
        for handoff_config in self.handoffs:
            handoff_tool = self._create_handoff_tool(handoff_config)
            self.tools[handoff_tool.name] = handoff_tool
            logger.info(f"Added handoff tool '{handoff_tool.name}' to '{self.name}'")

        self.logger = logging.getLogger(f"agnt5.agent.{name}")

        # Define schemas based on the run method signature
        # Input: user_message (string)
        self.input_schema = {
            "type": "object",
            "properties": {
                "user_message": {"type": "string"}
            },
            "required": ["user_message"]
        }
        # Output: AgentResult with output and tool_calls
        self.output_schema = {
            "type": "object",
            "properties": {
                "output": {"type": "string"},
                "tool_calls": {
                    "type": "array",
                    "items": {"type": "object"}
                }
            }
        }

        # Store metadata
        self.metadata = {
            "description": instructions,
            "model": model
        }

    def to_tool(self, description: Optional[str] = None) -> Tool:
        """Convert this agent to a Tool that can be used by other agents.

        This enables agents-as-tools pattern where one agent can invoke another
        agent as if it were a regular tool.

        Args:
            description: Optional custom description (defaults to agent instructions)

        Returns:
            Tool instance that wraps this agent

        Example:
            ```python
            research_agent = Agent(
                name="researcher",
                model="openai/gpt-4o-mini",
                instructions="You are a research specialist."
            )

            # Use research agent as a tool for another agent
            coordinator = Agent(
                name="coordinator",
                model="openai/gpt-4o-mini",
                instructions="Coordinate tasks using specialist agents.",
                tools=[research_agent.to_tool()]
            )
            ```
        """
        agent_name = self.name

        # Handler that runs the agent
        async def agent_tool_handler(ctx: Context, user_message: str) -> str:
            """Execute agent and return output."""
            ctx.logger.info(f"Invoking agent '{agent_name}' as tool")

            # Run the agent with the user message
            result = await self.run(user_message, context=ctx)

            return result.output

        # Create tool with agent's schema
        tool_description = description or self.instructions or f"Agent: {self.name}"

        agent_tool = Tool(
            name=self.name,
            description=tool_description,
            handler=agent_tool_handler,
            input_schema=self.input_schema,
            auto_schema=False,
        )

        return agent_tool

    def _create_handoff_tool(self, handoff_config: Handoff, current_messages_callback: Optional[Callable] = None) -> Tool:
        """Create a tool for handoff to another agent.

        Args:
            handoff_config: Handoff configuration
            current_messages_callback: Optional callback to get current conversation messages

        Returns:
            Tool instance that executes the handoff
        """
        target_agent = handoff_config.agent
        tool_name = handoff_config.tool_name

        # Handler that executes the handoff
        async def handoff_handler(ctx: Context, message: str) -> Dict[str, Any]:
            """Transfer control to target agent."""
            ctx.logger.info(
                f"Handoff from '{self.name}' to '{target_agent.name}': {message}"
            )

            # If we should pass conversation history, add it to context
            if handoff_config.pass_full_history:
                # Get current conversation from the agent's run loop
                # (This will be set when we detect the handoff in run())
                conversation_history = getattr(ctx, '_agent_data', {}).get("_current_conversation", [])

                if conversation_history:
                    ctx.logger.info(
                        f"Passing {len(conversation_history)} messages to target agent"
                    )
                    # Store in context for target agent to optionally use
                    if not hasattr(ctx, '_agent_data'):
                        ctx._agent_data = {}
                    ctx._agent_data["_handoff_conversation_history"] = conversation_history

            # Execute target agent with the message and shared context
            result = await target_agent.run(message, context=ctx)

            # Store handoff metadata - this signals that a handoff occurred
            handoff_data = {
                "_handoff": True,
                "from_agent": self.name,
                "to_agent": target_agent.name,
                "message": message,
                "output": result.output,
                "tool_calls": result.tool_calls,
            }

            if not hasattr(ctx, '_agent_data'):
                ctx._agent_data = {}
            ctx._agent_data["_handoff_result"] = handoff_data

            # Return the handoff data (will be detected in run() loop)
            return handoff_data

        # Create tool with handoff schema
        handoff_tool = Tool(
            name=tool_name,
            description=handoff_config.description,
            handler=handoff_handler,
            input_schema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "Message or task to pass to the target agent"
                    }
                },
                "required": ["message"]
            },
            auto_schema=False,
        )

        return handoff_tool

    async def run(
        self,
        user_message: str,
        context: Optional[Context] = None,
    ) -> AgentResult:
        """Run agent to completion.

        Args:
            user_message: User's input message
            context: Optional context (auto-created if not provided)

        Returns:
            AgentResult with output and execution details

        Example:
            ```python
            result = await agent.run("Analyze recent tech news")
            print(result.output)
            ```
        """
        # Create or adapt context
        if context is None:
            # Standalone execution - create AgentContext
            import uuid
            run_id = f"agent-{self.name}-{uuid.uuid4().hex[:8]}"
            context = AgentContext(
                run_id=run_id,
                agent_name=self.name,
            )
        elif isinstance(context, AgentContext):
            # Already AgentContext - use as-is
            pass
        elif hasattr(context, '_workflow_entity'):
            # WorkflowContext - create AgentContext that inherits state
            import uuid
            run_id = f"{context.run_id}:agent:{self.name}"
            context = AgentContext(
                run_id=run_id,
                agent_name=self.name,
                session_id=context.run_id,  # Share workflow's session
                parent_context=context,
            )
        else:
            # FunctionContext or other - create new AgentContext
            import uuid
            run_id = f"{context.run_id}:agent:{self.name}"
            context = AgentContext(
                run_id=run_id,
                agent_name=self.name,
            )

        # Load conversation history from state (if AgentContext)
        if isinstance(context, AgentContext):
            messages: List[Message] = await context.get_conversation_history()
            # Add new user message
            messages.append(Message.user(user_message))
            # Save updated conversation
            await context.save_conversation_history(messages)
        else:
            # Fallback for non-AgentContext (shouldn't happen with code above)
            messages = [Message.user(user_message)]

        # Create span for agent execution with trace linking
        from ._core import create_span

        with create_span(
            self.name,
            "agent",
            context._runtime_context if hasattr(context, "_runtime_context") else None,
            {
                "agent.name": self.name,
                "agent.model": self.model_name,  # Use model_name (always a string)
                "agent.max_iterations": str(self.max_iterations),
            },
        ) as span:
            all_tool_calls: List[Dict[str, Any]] = []

            # Reasoning loop
            for iteration in range(self.max_iterations):
                # Build tool definitions for LLM
                tool_defs = [
                    ToolDefinition(
                        name=tool.name,
                        description=tool.description,
                        parameters=tool.input_schema,
                    )
                    for tool in self.tools.values()
                ]

                # Convert messages to dict format for lm.generate()
                messages_dict = []
                for msg in messages:
                    messages_dict.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })

                # Call LLM
                # Check if we have a legacy LanguageModel instance or need to create one
                if self._language_model is not None:
                    # Legacy API: use provided LanguageModel instance
                    request = GenerateRequest(
                        model="mock-model",  # Not used by MockLanguageModel
                        system_prompt=self.instructions,
                        messages=messages,
                        tools=tool_defs if tool_defs else [],
                    )
                    request.config.temperature = self.temperature
                    if self.max_tokens:
                        request.config.max_tokens = self.max_tokens
                    if self.top_p:
                        request.config.top_p = self.top_p
                    response = await self._language_model.generate(request)
                else:
                    # New API: model is a string, create internal LM instance
                    request = GenerateRequest(
                        model=self.model,
                        system_prompt=self.instructions,
                        messages=messages,
                        tools=tool_defs if tool_defs else [],
                    )
                    request.config.temperature = self.temperature
                    if self.max_tokens:
                        request.config.max_tokens = self.max_tokens
                    if self.top_p:
                        request.config.top_p = self.top_p

                    # Create internal LM instance for generation
                    # TODO: Use model_config when provided
                    from .lm import _LanguageModel
                    provider, model_name = self.model.split('/', 1)
                    internal_lm = _LanguageModel(provider=provider.lower(), default_model=None)
                    response = await internal_lm.generate(request)

                # Add assistant response to messages
                messages.append(Message.assistant(response.text))

                # Check if LLM wants to use tools
                if response.tool_calls:
                    self.logger.debug(f"Agent calling {len(response.tool_calls)} tool(s)")

                    # Store current conversation in context for potential handoffs
                    # Use a simple dict attribute since we don't need full state persistence for this
                    if not hasattr(context, '_agent_data'):
                        context._agent_data = {}
                    context._agent_data["_current_conversation"] = messages

                    # Execute tool calls
                    tool_results = []
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args_str = tool_call["arguments"]

                        # Track tool call
                        all_tool_calls.append(
                            {
                                "name": tool_name,
                                "arguments": tool_args_str,
                                "iteration": iteration + 1,
                            }
                        )

                        # Execute tool
                        try:
                            # Parse arguments
                            tool_args = json.loads(tool_args_str)

                            # Get tool
                            tool = self.tools.get(tool_name)
                            if not tool:
                                result_text = f"Error: Tool '{tool_name}' not found"
                            else:
                                # Execute tool
                                result = await tool.invoke(context, **tool_args)

                                # Check if this was a handoff
                                if isinstance(result, dict) and result.get("_handoff"):
                                    self.logger.info(
                                        f"Handoff detected to '{result['to_agent']}', "
                                        f"terminating current agent"
                                    )
                                    # Save conversation before returning
                                    if isinstance(context, AgentContext):
                                        await context.save_conversation_history(messages)
                                    # Return immediately with handoff result
                                    return AgentResult(
                                        output=result["output"],
                                        tool_calls=all_tool_calls + result.get("tool_calls", []),
                                        context=context,
                                        handoff_to=result["to_agent"],
                                        handoff_metadata=result,
                                    )

                                result_text = json.dumps(result) if result else "null"

                            tool_results.append(
                                {"tool": tool_name, "result": result_text, "error": None}
                            )

                        except Exception as e:
                            self.logger.error(f"Tool execution error: {e}")
                            tool_results.append(
                                {"tool": tool_name, "result": None, "error": str(e)}
                            )

                    # Add tool results to conversation
                    results_text = "\n".join(
                        [
                            f"Tool: {tr['tool']}\nResult: {tr['result']}"
                            if tr["error"] is None
                            else f"Tool: {tr['tool']}\nError: {tr['error']}"
                            for tr in tool_results
                        ]
                    )
                    messages.append(Message.user(f"Tool results:\n{results_text}\n\nPlease provide your final answer based on these results."))

                    # Continue loop for agent to process results

                else:
                    # No tool calls - agent is done
                    self.logger.debug(f"Agent completed after {iteration + 1} iterations")
                    # Save conversation before returning
                    if isinstance(context, AgentContext):
                        await context.save_conversation_history(messages)
                    return AgentResult(
                        output=response.text,
                        tool_calls=all_tool_calls,
                        context=context,
                    )

            # Max iterations reached
            self.logger.warning(f"Agent reached max iterations ({self.max_iterations})")
            final_output = messages[-1].content if messages else "No output generated"
            # Save conversation before returning
            if isinstance(context, AgentContext):
                await context.save_conversation_history(messages)
            return AgentResult(
                output=final_output,
                tool_calls=all_tool_calls,
                context=context,
            )


def agent(
    _func: Optional[Callable] = None,
    *,
    name: Optional[str] = None,
    model: Optional[LanguageModel] = None,
    instructions: Optional[str] = None,
    tools: Optional[List[Any]] = None,
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.7,
    max_iterations: int = 10,
) -> Callable:
    """
    Decorator to register a function as an agent and automatically register it.

    This decorator allows you to define agents as functions that create and return Agent instances.
    The agent will be automatically registered in the AgentRegistry for discovery by the worker.

    Args:
        name: Agent name (defaults to function name)
        model: Language model instance (required if not provided in function)
        instructions: System instructions (required if not provided in function)
        tools: List of tools available to the agent
        model_name: Model name to use
        temperature: LLM temperature
        max_iterations: Maximum reasoning iterations

    Returns:
        Decorated function that returns an Agent instance

    Example:
        ```python
        from agnt5 import agent, tool
        from agnt5.lm import OpenAILanguageModel

        @agent(
            name="research_agent",
            model=OpenAILanguageModel(),
            instructions="You are a research assistant.",
            tools=[search_web, analyze_data]
        )
        def create_researcher():
            # Agent is created and registered automatically
            pass

        # Or create agent directly
        @agent
        def my_agent():
            from agnt5.lm import OpenAILanguageModel
            return Agent(
                name="my_agent",
                model=OpenAILanguageModel(),
                instructions="You are a helpful assistant."
            )
        ```
    """

    def decorator(func: Callable) -> Callable:
        # Determine agent name
        agent_name = name or func.__name__

        # Create the agent
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Agent:
            # Check if function returns an Agent
            result = func(*args, **kwargs)
            if isinstance(result, Agent):
                # Function creates its own agent
                agent_instance = result
            elif model is not None and instructions is not None:
                # Create agent from decorator parameters
                agent_instance = Agent(
                    name=agent_name,
                    model=model,
                    instructions=instructions,
                    tools=tools,
                    model_name=model_name,
                    temperature=temperature,
                    max_iterations=max_iterations,
                )
            else:
                raise ValueError(
                    f"Agent decorator for '{agent_name}' requires either "
                    "the decorated function to return an Agent instance, "
                    "or 'model' and 'instructions' parameters to be provided"
                )

            # Register agent
            AgentRegistry.register(agent_instance)
            return agent_instance

        # Create agent immediately and store reference
        agent_instance = wrapper()

        # Return the agent instance itself (so it can be used directly)
        return agent_instance

    if _func is None:
        return decorator
    return decorator(_func)
