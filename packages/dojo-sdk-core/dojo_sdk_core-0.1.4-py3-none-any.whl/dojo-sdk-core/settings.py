import os

from dotenv import load_dotenv

from dojo_sdk_core.models import SettingsConfig

load_dotenv()


_DEFAULT_HTTP_ENDPOINT = "https://orchestrator.trydojo.ai/api/v1"


def _resolve_http_endpoint() -> str:
    """Resolve the HTTP endpoint for the Dojo backend."""

    return os.getenv("DOJO_HTTP_ENDPOINT") or _DEFAULT_HTTP_ENDPOINT


def _derive_ws_endpoint(http_endpoint: str) -> str:
    """Derive a websocket endpoint from the provided HTTP endpoint."""

    if not http_endpoint:
        return "ws://localhost:8765/api/v1/jobs"

    normalized = http_endpoint.rstrip("/")
    if normalized.startswith("https://"):
        normalized = "wss://" + normalized[len("https://") :]
    elif normalized.startswith("http://"):
        normalized = "ws://" + normalized[len("http://") :]

    if not normalized.endswith("/jobs"):
        normalized = f"{normalized}/jobs"

    return normalized


_http_endpoint = _resolve_http_endpoint()
_ws_endpoint = os.getenv("DOJO_WEBSOCKET_ENDPOINT") or _derive_ws_endpoint(_http_endpoint)

settings = SettingsConfig(
    anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
    openai_api_key=os.getenv("OPENAI_API_KEY", ""),
    openai_api_url=os.getenv("OPENAI_API_URL", ""),
    # TODO: switch to prod endpoint as default
    dojo_websocket_endpoint=_ws_endpoint,
    dojo_http_endpoint=_http_endpoint,
)
