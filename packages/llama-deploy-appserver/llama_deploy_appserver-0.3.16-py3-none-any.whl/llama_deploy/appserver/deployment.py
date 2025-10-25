import asyncio
import json
import logging
import os
from typing import Any, Tuple
from urllib.parse import quote_plus

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from llama_deploy.appserver.deployment_config_parser import get_deployment_config
from llama_deploy.appserver.settings import ApiserverSettings, settings
from llama_deploy.appserver.types import generate_id
from llama_deploy.appserver.workflow_loader import DEFAULT_SERVICE_ID
from llama_deploy.appserver.workflow_store.agent_data_store import AgentDataStore
from llama_deploy.core.deployment_config import DeploymentConfig
from starlette.requests import Request
from starlette.responses import HTMLResponse
from starlette.routing import Route
from workflows import Context, Workflow
from workflows.handler import WorkflowHandler
from workflows.server import SqliteWorkflowStore, WorkflowServer
from workflows.server.abstract_workflow_store import EmptyWorkflowStore

logger = logging.getLogger()


class DeploymentError(Exception): ...


class Deployment:
    def __init__(
        self,
        workflows: dict[str, Workflow],
    ) -> None:
        """Creates a Deployment instance.

        Args:
            config: The configuration object defining this deployment
            root_path: The path on the filesystem used to store deployment data
            local: Whether the deployment is local. If true, sources won't be synced
        """

        self._default_service: str | None = workflows.get(DEFAULT_SERVICE_ID)
        self._service_tasks: list[asyncio.Task] = []
        # Ready to load services
        self._workflow_services: dict[str, Workflow] = workflows
        self._contexts: dict[str, Context] = {}
        self._handlers: dict[str, WorkflowHandler] = {}
        self._handler_inputs: dict[str, str] = {}

    @property
    def default_service(self) -> Workflow | None:
        return self._default_service

    @property
    def name(self) -> str:
        """Returns the name of this deployment."""
        return self._name

    @property
    def service_names(self) -> list[str]:
        """Returns the list of service names in this deployment."""
        return list(self._workflow_services.keys())

    async def run_workflow(
        self, service_id: str, session_id: str | None = None, **run_kwargs: dict
    ) -> Any:
        workflow = self._workflow_services[service_id]
        if session_id:
            context = self._contexts[session_id]
            return await workflow.run(context=context, **run_kwargs)

        if run_kwargs:
            return await workflow.run(**run_kwargs)

        return await workflow.run()

    def run_workflow_no_wait(
        self, service_id: str, session_id: str | None = None, **run_kwargs: dict
    ) -> Tuple[str, str]:
        workflow = self._workflow_services[service_id]
        if session_id:
            context = self._contexts[session_id]
            handler = workflow.run(context=context, **run_kwargs)
        else:
            handler = workflow.run(**run_kwargs)
            session_id = generate_id()
            self._contexts[session_id] = handler.ctx or Context(workflow)

        handler_id = generate_id()
        self._handlers[handler_id] = handler
        self._handler_inputs[handler_id] = json.dumps(run_kwargs)
        return handler_id, session_id

    def create_workflow_server(
        self, deployment_config: DeploymentConfig, settings: ApiserverSettings
    ) -> WorkflowServer:
        persistence = EmptyWorkflowStore()
        if settings.persistence == "local":
            logger.info("Using local sqlite persistence for workflows")
            persistence = SqliteWorkflowStore(
                settings.local_persistence_path or "workflows.db"
            )
        elif settings.persistence == "cloud" or (
            # default to cloud if api key is present to use
            settings.persistence is None and os.getenv("LLAMA_CLOUD_API_KEY")
        ):
            logger.info("Using agent data cloud persistence for workflows")
            persistence = AgentDataStore(deployment_config, settings)
        else:
            logger.info("Not persisting workflows")
        server = WorkflowServer(workflow_store=persistence)
        for service_id, workflow in self._workflow_services.items():
            server.add_workflow(service_id, workflow)
        return server

    def mount_workflow_server(self, app: FastAPI) -> WorkflowServer:
        config = get_deployment_config()
        server = self.create_workflow_server(config, settings)

        for route in server.app.routes:
            # add routes directly rather than mounting, so that we can share a root (only one ASGI app can be mounted at a path)
            if isinstance(route, Route):
                app.add_api_route(
                    f"/deployments/{config.name}{route.path}",
                    route.endpoint,
                    name=f"{config.name}_{route.name}",
                    methods=route.methods,
                    include_in_schema=True,  # change to false when schemas are added to workflow server
                    tags=["workflows"],
                )

        @app.get("/debugger", include_in_schema=False)
        @app.get("/debugger/", include_in_schema=False)
        def redirect_to_debugger(request: Request) -> RedirectResponse:
            return RedirectResponse(
                "/debugger/index.html?api=" + quote_plus("/deployments/" + config.name)
            )

        @app.get("/debugger/index.html", include_in_schema=False)
        def serve_debugger(api: str | None = None):
            if not api:
                return RedirectResponse(
                    "/debugger/index.html?api="
                    + quote_plus("/deployments/" + config.name)
                )
            else:
                return HTMLResponse("""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>workflow-debugger</title>
    <script type="module" crossorigin src="https://cdn.jsdelivr.net/npm/@llamaindex/workflow-debugger@latest/dist/app.js"></script>
    <link rel="stylesheet" crossorigin href="https://cdn.jsdelivr.net/npm/@llamaindex/workflow-debugger@latest/dist/app.css">
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
""")

        return server
