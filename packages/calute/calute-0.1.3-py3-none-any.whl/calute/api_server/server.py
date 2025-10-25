# Copyright 2025 The EasyDeL/Calute Author @erfanzar (Erfan Zare Chavoshi).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


"""Main API server class for the modular Calute API server."""

from __future__ import annotations

from typing import Any

import uvicorn
from fastapi import FastAPI

from calute import Calute
from calute.cortex import CortexAgent
from calute.llms.base import BaseLLM
from calute.types import Agent

from .completion_service import CompletionService
from .cortex_completion_service import CortexCompletionService
from .routers import ChatRouter, HealthRouter, ModelsRouter


class CaluteAPIServer:
    """Modular FastAPI server that provides OpenAI-compatible API for Calute agents.

    This server exposes registered Calute agents through HTTP endpoints that follow
    the OpenAI API specification, allowing seamless integration with OpenAI client libraries.

    The server is designed with a modular architecture:
    - Separate routers for different endpoint groups
    - Dedicated service for completion logic
    - Message conversion utilities
    - Centralized models for request/response handling

    Attributes:
        calute: The Calute instance managing agents
        agents: Dictionary mapping agent IDs to Agent objects
        app: FastAPI application instance
        completion_service: Service for handling chat completions

    Methods:
        register_agent: Register an agent to be available via API
        run: Start the API server

    Example:
        >>> from calute import Calute
        >>> from calute.api_server import CaluteAPIServer
        >>>
        >>> calute = Calute(client=openai_client)
        >>> server = CaluteAPIServer(calute)
        >>> server.register_agent(my_agent)
        >>> server.run(port=8000)
    """

    def __init__(
        self,
        calute_instance: Calute | None = None,
        llm: BaseLLM | None = None,
        can_overide_samplings: bool = False,
        enable_cortex: bool = False,
        use_universal_agent: bool = True,
    ):
        """Initialize the API server.

        Args:
            calute_instance: The Calute instance to use for agent management
            llm: LLM instance for Cortex agents
            can_overide_samplings: Whether to allow overriding sampling parameters
            enable_cortex: Whether to enable Cortex endpoints
            use_universal_agent: Whether to include UniversalAgent in Cortex
        """
        self.calute = calute_instance
        self.llm = llm
        self.agents: dict[str, Agent] = {}
        self.cortex_agents: list[CortexAgent] = []
        self.enable_cortex = enable_cortex

        title = "Calute API Server"
        if enable_cortex:
            title += " with Cortex"

        self.app = FastAPI(
            title=title,
            description="OpenAI-compatible API server for Calute agents with optional Cortex support",
            version="2.0.0",
        )

        if self.calute:
            self.completion_service = CompletionService(self.calute, can_overide_samplings=can_overide_samplings)
        else:
            self.completion_service = None

        if enable_cortex and llm:
            self.cortex_completion_service = CortexCompletionService(
                llm=llm,
                agents=self.cortex_agents,
                use_universal_agent=use_universal_agent,
                verbose=True,
            )
        else:
            self.cortex_completion_service = None

        self._routers_initialized = False

        if self.enable_cortex and self.cortex_completion_service:
            self._setup_routers()
            self._routers_initialized = True

    def register_agent(self, agent: Agent) -> None:
        """Register an agent to be available via API.

        Args:
            agent: The Agent instance to register

        Note:
            The agent will be available via its ID, name, or model as the model parameter
            in chat completion requests.
        """
        if not self.calute:
            raise ValueError("Calute instance required for registering regular agents")

        self.calute.register_agent(agent)
        agent_key = agent.id or agent.name or agent.model
        self.agents[agent_key] = agent

        if not self._routers_initialized:
            self._setup_routers()
            self._routers_initialized = True

    def register_cortex_agent(self, agent: CortexAgent) -> None:
        """Register a CortexAgent for orchestration.

        Args:
            agent: The CortexAgent instance to register

        Note:
            CortexAgents are used for multi-agent orchestration via Cortex endpoints.
        """
        if not self.enable_cortex:
            raise ValueError("Cortex must be enabled to register CortexAgents")

        self.cortex_agents.append(agent)

        if self.cortex_completion_service:
            self.cortex_completion_service.agents = self.cortex_agents

        if not self._routers_initialized:
            self._setup_routers()
            self._routers_initialized = True

    def _setup_routers(self) -> None:
        """Set up FastAPI routers for the API endpoints."""
        from .routers import UnifiedChatRouter

        if self.enable_cortex and self.cortex_completion_service:
            unified_router = UnifiedChatRouter(
                agents=self.agents,
                completion_service=self.completion_service,
                cortex_completion_service=self.cortex_completion_service,
            )
            self.app.include_router(unified_router.router, tags=["chat"])
        elif self.completion_service and self.agents:
            chat_router = ChatRouter(self.agents, self.completion_service)
            self.app.include_router(chat_router.router, tags=["chat"])

        if self.completion_service or self.cortex_completion_service:
            all_models = self._get_all_models()
            models_router = ModelsRouter(all_models)
            health_router = HealthRouter(all_models)
            self.app.include_router(models_router.router, tags=["models"])
            self.app.include_router(health_router.router, tags=["health"])

    def _get_all_models(self) -> dict[str, Any]:
        """Get all available models including Cortex models.

        Returns:
            Dictionary mapping model names to their configurations
        """
        models = dict(self.agents)

        if self.enable_cortex:
            cortex_base_models = {
                "cortex": {"type": "cortex", "mode": "instruction"},
                "cortex-instruct": {"type": "cortex", "mode": "instruction"},
                "cortex-task": {"type": "cortex", "mode": "task"},
                "cortex-task-parallel": {"type": "cortex", "mode": "task", "process": "parallel"},
                "cortex-task-hierarchical": {"type": "cortex", "mode": "task", "process": "hierarchical"},
            }

            prefixes = ["", "calute-", "api-", "v1-"]
            for prefix in prefixes:
                for model_name, config in cortex_base_models.items():
                    full_name = f"{prefix}{model_name}" if prefix else model_name
                    models[full_name] = config

        return models

    def run(self, host: str = "0.0.0.0", port: int = 11881, **kwargs) -> None:
        """Run the API server.

        Args:
            host: Host to bind the server to (default: "0.0.0.0")
            port: Port to bind the server to (default: 11881)
            **kwargs: Additional arguments passed to uvicorn.run()
        """
        if not self._routers_initialized:
            if self.enable_cortex and self.cortex_completion_service:
                self._setup_routers()
                self._routers_initialized = True
            else:
                raise RuntimeError(
                    "No agents registered. Please register at least one agent before starting the server."
                )

        uvicorn.run(self.app, host=host, port=port, **kwargs)

    @classmethod
    def create_server(
        cls,
        client: Any,
        agents: list[Agent] | None | Agent = None,
        can_overide_samplings: bool = False,
        **calute_kwargs,
    ) -> CaluteAPIServer:
        """Create a Calute API server with the given client and agents.

        This is a convenience factory function that creates a Calute instance and
        API server, then registers the provided agents.

        Args:
            client: OpenAI-compatible client instance
            agents: List of agents to register (optional)
            **calute_kwargs: Additional arguments passed to Calute constructor

        Returns:
            CaluteAPIServer instance ready to run

        Example:
            >>> import openai
            >>> from calute.types import Agent
            >>> from calute.api_server import create_server
            >>>
            >>> client = openai.OpenAI(api_key="key", base_url="url")
            >>> agent = Agent(id="assistant", model="gpt-4", instructions="Help users")
            >>> server = create_server(client, agents=[agent])
            >>> server.run(port=8000)
        """
        calute = Calute(client=client, **calute_kwargs)
        server = CaluteAPIServer(calute, can_overide_samplings)
        if isinstance(agents, Agent):
            agents = [agents]
        if agents:
            for agent in agents:
                server.register_agent(agent)

        return server
