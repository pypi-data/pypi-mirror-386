import asyncio
import importlib
import json
import os
import tempfile
from collections.abc import Callable
from contextlib import nullcontext
from typing import Any

from connector_sdk_types.generated import AppInfoResponse
from fastapi import FastAPI, Request

from connector.ca_certs import is_windows, set_python_to_use_system_ca_certificates
from connector.httpx_rewrite import proxy_settings
from connector.oai.integration import Integration
from connector.observability.logging import set_logger_config
from connector.observability.observer import Observations, Observer
from connector.utils import proxy_utils

FLOWS_V2_EXECUTION_ID_OBSERVABILITY_HEADER = "X-Lumos-Observability-flows_v2_execution_id"
DAGSTER_RUN_ID_OBSERVABILITY_HEADER = "X-Lumos-Observability-dagster.run_id"


def _always_false(_: Request) -> bool:
    return False


def create_req_handler(
    capability: str,
    integration: Integration,
    use_proxy: bool,
    use_executor_dispatch: Callable[[Request], bool],
):
    async def req_handler(request: Request):
        body = await request.body()
        req_str = body.decode()
        integration.handle_errors = True

        observations: Observations = {
            "flows_v2_execution_id": request.headers.get(
                FLOWS_V2_EXECUTION_ID_OBSERVABILITY_HEADER,
                "",
            )
        }
        if run_id := request.headers.get(DAGSTER_RUN_ID_OBSERVABILITY_HEADER, ""):
            observations["dagster"] = {"run_id": run_id}

        proxy_cm = (
            proxy_settings(
                proxy_url=proxy_utils.get_proxy_url(),
                proxy_headers={
                    "X-Lumos-Proxy-Auth": (await proxy_utils.get_proxy_token_async()).token,
                },
            )
            if use_proxy
            else nullcontext()
        )

        dispatch = integration.dispatch
        if use_executor_dispatch(request):
            dispatch = integration.executor_dispatch

        with proxy_cm, Observer.observe(observations):
            response = await dispatch(capability, req_str)

        return json.loads(response)

    return req_handler


def collect_integration_routes(
    integration: Integration,
    prefix_app_id: bool = False,
    use_proxy: bool = False,
    use_executor_dispatch: Callable[[Request], bool] = _always_false,
):
    """Create API endpoint for each method in integration."""
    from fastapi import APIRouter

    router = APIRouter()
    for capability_name, _ in integration.capabilities.items():
        prefix = f"/{integration.app_id}" if prefix_app_id else ""
        # replace `-` in prefix (e.g. app_id) and capability name
        route = f"{prefix}/{capability_name}".replace("-", "_")
        handler = create_req_handler(
            capability_name,
            integration,
            use_proxy=use_proxy,
            use_executor_dispatch=use_executor_dispatch,
        )
        router.add_api_route(route, handler, methods=["POST"])

    return router


def create_app() -> FastAPI:
    """Create a FastAPI app for the integration, if a factory is needed (hot reload)."""
    integration_id = os.environ.get("HTTP_SERVER_INTEGRATION_ID")
    if not integration_id:
        raise ValueError("HTTP_SERVER_INTEGRATION_ID environment variable is not set!")

    integration = load_integration(integration_id)
    set_logger_config(integration.app_id)
    if is_windows():
        set_python_to_use_system_ca_certificates()
    app = FastAPI()

    def get_schema():
        try:
            temp_dir = tempfile.gettempdir()
            schema_path = os.path.join(temp_dir, f"{integration.app_id}.json")
            with open(schema_path) as f:
                openapi_schema = json.load(f)
            return openapi_schema
        except OSError:
            print(f"Error retrieving OAS schema for {integration.app_id}")
            return {}

    app.openapi = get_schema  # type: ignore
    router = collect_integration_routes(
        integration,
        use_proxy=os.environ.get("HTTP_SERVER_USE_PROXY", "False") == "True",
    )
    app.include_router(router)
    return app


def load_integration(integration_id: str):
    """Import the integration module and return the integration object, uvicorn needs a import when running with reload True."""
    integration_module_name = integration_id.replace("-", "_")
    try:
        module = importlib.import_module(f"{integration_module_name}.integration")
        return module.integration
    except ModuleNotFoundError as e:
        raise ValueError(f"Integration {integration_module_name} not found") from e


def create_oas_schema(integration: Integration) -> dict[str, Any]:
    """Collect the OAS schema for the integration."""
    try:
        app_info = asyncio.run(integration.dispatch("app_info", json.dumps({"request": {}})))
        response = AppInfoResponse.model_validate_json(app_info)
        schema = response.response.app_schema
    except Exception as e:
        print(f"Error collecting OAS schema for {integration.app_id}:")
        print(e)
        schema = {}

    if schema:
        try:
            temp_dir = tempfile.gettempdir()
            schema_path = os.path.join(temp_dir, f"{integration.app_id}.json")
            with open(schema_path, "w") as f:
                json.dump(schema, f)
        except OSError:
            print(f"Error retrieving OAS schema for {integration.app_id}")

    return schema


def runserver(port: int, integration: Integration, reload: bool = False, use_proxy: bool = False):
    try:
        import uvicorn

        # Generate OAS for integration
        schema = create_oas_schema(integration)

        if reload:
            os.environ["HTTP_SERVER_INTEGRATION_ID"] = integration.app_id
            os.environ["HTTP_SERVER_USE_PROXY"] = str(use_proxy)
        else:
            app = FastAPI()
            app.openapi = lambda: schema  # type: ignore
            router = collect_integration_routes(integration, use_proxy=use_proxy)
            app.include_router(router)

        uvicorn.run(
            app=app if not reload else "connector.http_server:create_app",
            factory=True if reload else False,
            port=port,
            reload=reload,
            reload_dirs=[
                "projects/libs/python/connector-sdk",
                f"projects/connectors/python/{integration.app_id}",
            ]
            if reload
            else None,
        )
    except KeyboardInterrupt:
        pass
