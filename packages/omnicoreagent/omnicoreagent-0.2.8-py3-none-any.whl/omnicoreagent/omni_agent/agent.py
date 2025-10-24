import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from omnicoreagent.core.agents.react_agent import ReactAgent
from omnicoreagent.core.agents.types import AgentConfig as ReactAgentConfig
from omnicoreagent.mcp_omni_connect.client import Configuration, MCPClient
from omnicoreagent.core.llm import LLMConnection
from omnicoreagent.core.memory_store.memory_router import MemoryRouter
from omnicoreagent.omni_agent.config import (
    config_transformer,
    ModelConfig,
    MCPToolConfig,
    AgentConfig,
)
from omnicoreagent.omni_agent.prompts.prompt_builder import OmniAgentPromptBuilder
from omnicoreagent.omni_agent.prompts.react_suffix import SYSTEM_SUFFIX
from omnicoreagent.core.events.event_router import EventRouter
from omnicoreagent.core.tools.semantic_tools import SemanticToolManager


class OmniAgent:
    """
    A simple, user-friendly interface for creating and using MCP agents.

    This class provides a high-level API that abstracts away the complexity
    of MCP client configuration and agent creation.
    """

    def __init__(
        self,
        name: str,
        system_instruction: str,
        model_config: Union[Dict[str, Any], ModelConfig],
        mcp_tools: List[Union[Dict[str, Any], MCPToolConfig]] = None,
        local_tools: Optional[Any] = None,  # LocalToolsIntegration instance
        agent_config: Optional[Union[Dict[str, Any], AgentConfig]] = None,
        embedding_config: Optional[Dict[str, Any]] = None,
        memory_router: Optional[MemoryRouter] = None,
        event_router: Optional[EventRouter] = None,
        debug: bool = False,
    ):
        """
        Initialize the OmniAgent with user-friendly configuration.

        Args:
            name: Name of the agent
            system_instruction: System instruction for the agent
            model_config: Model configuration (dict or ModelConfig)
            mcp_tools: List of MCP tool configurations (optional)
            local_tools: LocalToolsIntegration instance (optional)
            agent_config: Optional agent configuration
            embedding_config: Optional embedding configuration
            memory_router: Optional memory router (MemoryRouter)
            event_router: Optional event router (EventRouter)
            debug: Enable debug logging
        """
        # Core attributes
        self.name = name
        self.system_instruction = system_instruction
        self.model_config = model_config
        self.mcp_tools = mcp_tools or []
        self.local_tools = local_tools
        self.agent_config = agent_config
        self.embedding_config = embedding_config or {}

        self.debug = debug
        self.memory_router = memory_router or MemoryRouter(
            memory_store_type="in_memory"
        )
        self.event_router = event_router or EventRouter(event_store_type="in_memory")

        # Internal components
        self.config_transformer = config_transformer
        self.prompt_builder = OmniAgentPromptBuilder(SYSTEM_SUFFIX)
        self.agent = None
        self.mcp_client = None
        self.llm_connection = None

        # Transform user config to internal format
        self.internal_config = self._create_internal_config()

        # Create agent
        self._create_agent()

    def _create_internal_config(self) -> Dict[str, Any]:
        """Transform user configuration to internal format"""
        agent_config_with_name = self._prepare_agent_config()

        internal_config = config_transformer.transform_config(
            model_config=self.model_config,
            mcp_tools=self.mcp_tools,
            agent_config=agent_config_with_name,
            embedding_config=self.embedding_config,
        )

        # Save to hidden location
        self._save_config_hidden(internal_config)

        return internal_config

    def _prepare_agent_config(self) -> Dict[str, Any]:
        """Prepare agent config with the agent name included"""
        if self.agent_config:
            if isinstance(self.agent_config, dict):
                agent_config_dict = self.agent_config.copy()
                agent_config_dict["agent_name"] = self.name
                return agent_config_dict
            else:
                agent_config_dict = self.agent_config.__dict__.copy()
                agent_config_dict["agent_name"] = self.name
                return agent_config_dict
        else:
            # Default agent config with the agent name
            return {
                "agent_name": self.name,
                "tool_call_timeout": 30,
                "max_steps": 15,
                "request_limit": 0,
                "total_tokens_limit": 0,
                "enable_tools_knowledge_base": False,
                "memory_config": {"mode": "token_budget", "value": 30000},
            }

    def _save_config_hidden(self, config: Dict[str, Any]):
        """Save config to hidden location with agent-specific filename"""
        hidden_dir = Path(".omniagent_config")
        hidden_dir.mkdir(exist_ok=True)

        # Use agent name to create unique config file
        safe_agent_name = (
            self.name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        )
        hidden_config_path = hidden_dir / f"servers_config_{safe_agent_name}.json"
        self.config_transformer.save_config(config, str(hidden_config_path))

        # Store the config path for cleanup
        self._config_file_path = hidden_config_path

    def _create_agent(self):
        """Create the appropriate agent based on configuration"""
        # Create shared configuration
        shared_config = Configuration()

        # Initialize MCP client only if MCP tools are provided
        if self.mcp_tools:
            self.mcp_client = MCPClient(
                config=shared_config,
                debug=self.debug,
                config_filename=str(self._config_file_path),
            )
            # Use the LLMConnection from MCPClient to avoid duplication
            self.llm_connection = self.mcp_client.llm_connection
        else:
            self.mcp_client = None
            # Create LLMConnection only if no MCP client exists
            self.llm_connection = LLMConnection(
                shared_config, config_filename=str(self._config_file_path)
            )

        # Get agent config from internal config
        agent_config_dict = self.internal_config["AgentConfig"]
        agent_settings = ReactAgentConfig(**agent_config_dict)

        # Set memory config
        if self.memory_router:
            self.memory_router.set_memory_config(
                mode=agent_settings.memory_config["mode"],
                value=agent_settings.memory_config["value"],
            )

        # Create ReactAgent
        self.agent = ReactAgent(config=agent_settings)

    def generate_session_id(self) -> str:
        """Generate a new session ID for the session"""
        return f"omni_agent_{self.name}_{uuid.uuid4().hex[:8]}"

    async def connect_mcp_servers(self):
        """Connect to MCP servers if MCP tools are configured"""
        if self.mcp_client and self.mcp_tools:
            # Use the config_filename that's already stored in the MCPClient
            await self.mcp_client.connect_to_servers(self.mcp_client.config_filename)
            # also connect all the tools to the tools knowledge base if its enabled
            if self.agent.enable_tools_knowledge_base:
                llm_connection = self.llm_connection
                store_tool = self.memory_router.store_tool
                tool_exists = self.memory_router.tool_exists
                mcp_tools = self.mcp_client.available_tools if self.mcp_client else {}
                semantic_tools_manager = SemanticToolManager(
                    llm_connection=llm_connection
                )

                await semantic_tools_manager.batch_process_all_mcp_servers(
                    mcp_tools=mcp_tools,
                    store_tool=store_tool,
                    tool_exists=tool_exists,
                )

    async def run(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the agent with a query and optional session ID.

        Args:
            query: The user query
            session_id: Optional session ID for session continuity

        Returns:
            Dict containing response and session_id
        """
        # Generate session ID if not provided
        if not session_id:
            session_id = self.generate_session_id()

        omni_agent_prompt = self.prompt_builder.build(
            system_instruction=self.system_instruction
        )

        extra_kwargs = {
            "sessions": self.mcp_client.sessions if self.mcp_client else {},
            "mcp_tools": self.mcp_client.available_tools if self.mcp_client else {},
            "local_tools": self.local_tools,
            "session_id": session_id,
        }

        # Run the agent with memory object directly
        response = await self.agent._run(
            system_prompt=omni_agent_prompt,
            query=query,
            llm_connection=self.llm_connection,
            add_message_to_history=self.memory_router.store_message,
            message_history=self.memory_router.get_messages,
            debug=self.debug,
            event_router=self.event_router.append,
            **extra_kwargs,
        )

        return {"response": response, "session_id": session_id, "agent_name": self.name}

    async def list_all_available_tools(self):
        """List all available tools (MCP and local)"""
        available_tools = []

        if self.mcp_client:
            for _, tools in self.mcp_client.available_tools.items():
                for tool in tools:
                    # check the type if dict or pydancit model
                    if isinstance(tool, dict):
                        available_tools.append(
                            {
                                "name": tool.get("name", ""),
                                "description": tool.get("description", ""),
                                "inputSchema": tool.get("inputSchema", {}),
                                "type": "mcp",
                            }
                        )
                    else:
                        available_tools.append(
                            {
                                "name": tool.name,
                                "description": tool.description,
                                "inputSchema": tool.inputSchema,
                                "type": "mcp",
                            }
                        )
        if self.local_tools:
            available_tools.extend(self.local_tools.get_available_tools())
        return available_tools

    async def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Get session history for a specific session ID"""
        if not self.memory_router:
            return []

        return await self.memory_router.get_messages(
            session_id=session_id, agent_name=self.name
        )

    async def clear_session_history(self, session_id: Optional[str] = None):
        """Clear session history for a specific session ID or all history"""
        if not self.memory_router:
            return

        if session_id:
            await self.memory_router.clear_memory(
                session_id=session_id, agent_name=self.name
            )
        else:
            await self.memory_router.clear_memory(agent_name=self.name)

    async def stream_events(self, session_id: str):
        async for event in self.event_router.stream(session_id=session_id):
            yield event

    async def get_events(self, session_id: str):
        return await self.event_router.get_events(session_id=session_id)

    # EventRouter methods exposed through OmniAgent
    def get_event_store_type(self) -> str:
        """Get the current event store type."""
        return self.event_router.get_event_store_type()

    def is_event_store_available(self) -> bool:
        """Check if the event store is available."""
        return self.event_router.is_available()

    def get_event_store_info(self) -> Dict[str, Any]:
        """Get information about the current event store."""
        return self.event_router.get_event_store_info()

    def switch_event_store(self, event_store_type: str):
        """Switch to a different event store type."""
        self.event_router.switch_event_store(event_store_type)

    def get_memory_store_type(self) -> str:
        """Get the current memory store type."""
        return self.memory_router.memory_store_type

    def swith_memory_store(self, memory_store_type: str):
        """Switch to a different memory store type."""
        self.memory_router.swith_memory_store(memory_store_type)

    async def cleanup(self):
        """Clean up resources"""
        if self.mcp_client:
            await self.mcp_client.cleanup()

        # Clean up config files
        self._cleanup_config()

    def _cleanup_config(self):
        """Clean up the agent-specific config file"""
        try:
            # Only clean up this agent's specific config file
            if hasattr(self, "_config_file_path") and self._config_file_path.exists():
                self._config_file_path.unlink()

            # If no more config files in directory, remove the directory
            hidden_dir = Path(".omniagent_config")
            if hidden_dir.exists() and not list(hidden_dir.glob("*.json")):
                hidden_dir.rmdir()
        except Exception:
            # Silently handle cleanup errors
            pass
