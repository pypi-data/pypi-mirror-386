"""Basic MCP mcp-agent app integration with OpenAI Apps SDK.

The server exposes widget-backed tools that render the UI bundle within the
client directory. Each handler returns the HTML shell via an MCP resource and
returns structured content so the ChatGPT client can hydrate the widget."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from random import choice
from typing import Any, Dict, List

from starlette.routing import Mount
from starlette.staticfiles import StaticFiles
import mcp.types as types
from mcp.server.fastmcp import FastMCP
import uvicorn
from mcp_agent.app import MCPApp
from pathlib import Path

from mcp_agent.server.app_server import create_mcp_server_for_app


@dataclass(frozen=True)
class CoinFlipWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


BUILD_DIR = Path(__file__).parent / "web" / "build"
ASSETS_DIR = BUILD_DIR / "static"

# Providing the JS and CSS to the app can be done in 1 of 2 ways:
# 1) Load the content as text from the static build files and inline them into the HTML template
# 2) (Preferred) Reference the static files served from the deployed server
# Since (2) depends on an initial deployment of the server, it is recommended to use approach (1) first
# and then switch to (2) once the server is deployed and its URL is available.
# (2) is preferred since (1) can lead to large HTML templates and potential for string escaping issues.


# Make sure these paths align with the build output paths (dynamic per build)
JS_PATH = ASSETS_DIR / "js" / "main.9c62c88b.js"
CSS_PATH = ASSETS_DIR / "css" / "main.57005a98.css"


# METHOD 1: Inline the JS and CSS into the HTML template
COIN_FLIP_JS = JS_PATH.read_text(encoding="utf-8")
COIN_FLIP_CSS = CSS_PATH.read_text(encoding="utf-8")

INLINE_HTML_TEMPLATE = f"""
<div id="coinflip-root"></div>
<style>
{COIN_FLIP_CSS}
</style>
<script type="module">
{COIN_FLIP_JS}
</script>
"""

# METHOD 2: Reference the static files from the deployed server
SERVER_URL = "https://<server_id>.deployments.mcp-agent.com"  # e.g. "https://15da9n6bk2nj3wiwf7ghxc2fy7sc6c8a.deployments.mcp-agent.com"
DEPLOYED_HTML_TEMPLATE = (
    '<div id="coinflip-root"></div>\n'
    f'<link rel="stylesheet" href="{SERVER_URL}/static/css/main.57005a98.css">\n'
    f'<script type="module" src="{SERVER_URL}/static/js/main.9c62c88b.js"></script>'
)


WIDGET = CoinFlipWidget(
    identifier="coin-flip",
    title="Flip a Coin",
    # OpenAI Apps heavily cache resource by URI, so use a date-based URI to bust the cache when updating the app.
    template_uri="ui://widget/coin-flip-10-22-2025-15-48.html",
    invoking="Preparing for coin flip",
    invoked="Flipping the coin...",
    html=INLINE_HTML_TEMPLATE,  # Use INLINE_HTML_TEMPLATE or DEPLOYED_HTML_TEMPLATE
    response_text="Flipped the coin! Click the coin to flip again.",
)


MIME_TYPE = "text/html+skybridge"

mcp = FastMCP(
    name="coinflip",
    stateless_http=True,
)
app = MCPApp(
    name="coinflip", description="UX for flipping a coin within an OpenAI chat", mcp=mcp
)


def _resource_description() -> str:
    return "Coin flip widget markup"


def _tool_meta() -> Dict[str, Any]:
    return {
        "openai/outputTemplate": WIDGET.template_uri,
        "openai/toolInvocation/invoking": WIDGET.invoking,
        "openai/toolInvocation/invoked": WIDGET.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "annotations": {
            "destructiveHint": False,
            "openWorldHint": False,
            "readOnlyHint": True,
        },
    }


def _embedded_widget_resource() -> types.EmbeddedResource:
    return types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=WIDGET.template_uri,
            mimeType=MIME_TYPE,
            text=WIDGET.html,
            title=WIDGET.title,
        ),
    )


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=WIDGET.identifier,
            title=WIDGET.title,
            inputSchema={"type": "object", "properties": {}},
            description=WIDGET.title,
            _meta=_tool_meta(),
        )
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=WIDGET.title,
            title=WIDGET.title,
            uri=WIDGET.template_uri,
            description=_resource_description(),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(),
        )
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=WIDGET.title,
            title=WIDGET.title,
            uriTemplate=WIDGET.template_uri,
            description=_resource_description(),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(),
        )
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    if str(req.params.uri) != WIDGET.template_uri:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=WIDGET.template_uri,
            mimeType=MIME_TYPE,
            text=WIDGET.html,
            _meta=_tool_meta(),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    if req.params.name != WIDGET.identifier:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {req.params.name}",
                    )
                ],
                isError=True,
            )
        )

    widget_resource = _embedded_widget_resource()
    meta: Dict[str, Any] = {
        "openai.com/widget": widget_resource.model_dump(mode="json"),
        "openai/outputTemplate": WIDGET.template_uri,
        "openai/toolInvocation/invoking": WIDGET.invoking,
        "openai/toolInvocation/invoked": WIDGET.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }

    flip_result = choice(["heads", "tails"])

    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=WIDGET.response_text,
                )
            ],
            structuredContent={"flipResult": flip_result},
            _meta=meta,
        )
    )


mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource


# NOTE: This main function is for local testing; it spins up the MCP server (SSE) and
# serves the static assets for the web client. You can view the tool results / resources
# in MCP Inspector.
# Client development/testing should be done using the development webserver spun up via `yarn start`
# in the `web/` directory.
async def main():
    async with app.run() as coinflip_app:
        mcp_server = create_mcp_server_for_app(coinflip_app)

        ASSETS_DIR = BUILD_DIR / "static"
        if not ASSETS_DIR.exists():
            raise FileNotFoundError(
                f"Assets directory not found at {ASSETS_DIR}. "
                "Please build the web client before running the server."
            )

        starlette_app = mcp_server.sse_app()

        # This serves the static css and js files referenced by the HTML
        starlette_app.routes.append(
            Mount("/static", app=StaticFiles(directory=ASSETS_DIR), name="static")
        )

        # This serves the main HTML file at the root path for the server
        starlette_app.routes.append(
            Mount(
                "/",
                app=StaticFiles(directory=BUILD_DIR, html=True),
                name="root",
            )
        )

        # Serve via uvicorn, mirroring FastMCP.run_sse_async
        config = uvicorn.Config(
            starlette_app,
            host=mcp_server.settings.host,
            port=int(mcp_server.settings.port),
        )
        server = uvicorn.Server(config)
        await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
