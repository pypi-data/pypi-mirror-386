import asyncio
from collections.abc import Iterable
import json
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path
import sys
from typing import Annotated, AsyncGenerator
from pyinstrument import Profiler
from pyinstrument.renderers import HTMLRenderer
from pyinstrument import processors
from clients import PiScorerClient, RetrievalClient
from data_model import (
    DebugInfo,
    Document,
    Params,
    SearchQuery,
    SearchResults,
    reset_ctx,
    set_ctx,
)
from data_model.piragbox_model import (
    get_pipeline,
    get_pipeline_param_defaults,
    list_pipelines,
)
from dotenv import load_dotenv
from fastapi import Request, Depends, FastAPI, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

load_dotenv()

# Add builtin_flows to sys.path if pi_flows is not already importable
# This allows using builtin flows by default, or custom flows via PYTHONPATH
try:
    import pi_flows  # noqa: F401
    print("Loaded pi_flows from PYTHONPATH", file=sys.stderr)
except ImportError:
    builtin_flows_path = Path(__file__).parent / "builtin_flows"
    sys.path.insert(0, str(builtin_flows_path))
    print(f"Added {builtin_flows_path} to sys.path for builtin flows", file=sys.stderr)
    import pi_flows  # noqa: F401

# Validate that at least one pipeline was registered
pipelines = list_pipelines()
if not pipelines:
    raise RuntimeError(
        "No search pipelines were registered!\n"
        "Expected pi_flows module to register at least one @piragbox decorated function.\n"
        "Check that your pi_flows module is properly configured."
    )

print(f"Registered {len(pipelines)} search pipeline(s): {', '.join(pipelines)}", file=sys.stderr)


@dataclass
class AppStateHolder:
    """Application state container for shared clients."""

    pi_scorer_client: PiScorerClient
    retrieval_client: RetrievalClient


def get_app_state() -> AppStateHolder:
    """Type-safe accessor for application state."""
    return app.state.app_state


AppState = Annotated[AppStateHolder, Depends(get_app_state)]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan hook to initialize and cleanup shared clients.
    """
    app.state.connection_manager = ConnectionManager()
    async with PiScorerClient() as pi_scorer_client, RetrievalClient() as retrieval_client:
        app.state.app_state = AppStateHolder(
            pi_scorer_client=pi_scorer_client,
            retrieval_client=retrieval_client,
        )
        yield

    await app.state.connection_manager.disconnect_all()
    print("All websockets disconnected.", file=sys.stderr)


app = FastAPI(title="Search Service", lifespan=lifespan)


@app.middleware("http")
async def profile_request(request: Request, call_next):
    if not request.query_params.get("profile", False):
        return await call_next(request)
    profiler = Profiler(async_mode='enabled')
    profiler.start()
    await call_next(request)
    profiler.stop()
    session = profiler.last_session
    if session is None:
        raise HTTPException(status_code=500, detail="Profiling session is None")
    renderer = HTMLRenderer()
    renderer.preprocessors.insert(0, processors.group_library_frames_processor)
    renderer.preprocessor_options = {"hide_regex": ".*/(starlette|httpx|asyncio)/.*"}
    return HTMLResponse(renderer.render(session))


async def bind_request_state_ctx(app_state: AppState) -> AsyncGenerator[None, None]:
    token = set_ctx(app_state)
    try:
        yield
    finally:
        reset_ctx(token)


def get_pi_scorer_client(app_state: AppState) -> PiScorerClient:
    """Dependency injection for PiScorerClient."""
    return app_state.pi_scorer_client


def get_retrieval_client(app_state: AppState) -> RetrievalClient:
    """Dependency injection for RetrievalClient."""
    return app_state.retrieval_client


@app.get("/")
async def root():
    return {"message": "Search Service API"}


class ConnectionManager:
    '''
    https://fastapi.tiangolo.com/advanced/websockets/#handling-disconnections-and-multiple-clients
    '''
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def disconnect_all(self):
        async with asyncio.TaskGroup() as tg:
            for websocket in self.active_connections:
                tg.create_task(websocket.close())

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await app.state.connection_manager.connect(websocket)

    search_flows = SearchMetadata(
        search_flows=[
            SearchFlow(
                name=search_fn_name, params=get_pipeline_param_defaults(search_fn_name)
            )
            for search_fn_name in list_pipelines()
        ]
    )
    await websocket.send_text(json.dumps({
        "type": "search_flows",
        "search_flows": search_flows.model_dump()
    }))

    while True:
        data = await websocket.receive_text()

        try:
            message = json.loads(data)
            match message["type"]:
                case "poll_search_flows":
                    await websocket.send_text(json.dumps({
                        "type": "search_flows",
                        "search_flows": search_flows.model_dump()["search_flows"]
                    }))
        except json.JSONDecodeError:
            print(file=sys.stderr)
            continue


def _rewrite_doc_content(doc: Document) -> Document:
    content = doc.content

    # If this doc uses a single 'text' field (string or dict), convert it to 'content'
    if "text" in content and isinstance(content["text"], (str, dict)):
        raw = content["text"]
        if isinstance(raw, str):
            try:
                payload = json.loads(raw)
            except Exception:
                payload = {"raw_text": raw}
        else:
            payload = dict(raw)
        content = payload  # replace with parsed content

    # Work on a copy to avoid mutating the original dict
    new_content = dict(content)

    # Rename "Title/Name" -> "name" if present
    if "Title/Name" in new_content:
        new_content["name"] = new_content.pop("Title/Name")

    # if "description" not in new_content:
    #    new_content["description"] = json.dumps(content)

    # Return a NEW Document (since Document is frozen)
    return doc.model_copy(update={"content": new_content})


@app.post("/search", dependencies=[Depends(bind_request_state_ctx)])
async def search(
    query: SearchQuery,
) -> SearchResults:
    """
    Execute a search query.
    """
    if len(list_pipelines()) == 0:
        raise HTTPException(
            status_code=422, detail="There is no registered ranking function!!!"
        )

    search_fn_name = query.query_params.get("search_fn", None)
    if search_fn_name is None and len(list_pipelines()) == 1:
        search_fn_name = list_pipelines()[0]
    if search_fn_name is None:
        raise HTTPException(
            status_code=422,
            detail=f'Must specify "search_fn" query param to be one of: {list_pipelines()}!!!',
        )
    if not isinstance(search_fn_name, str):
        raise HTTPException(
            status_code=422, detail='"search_fn" query param must be of type string!!!'
        )

    try:
        rank_pipeline = get_pipeline(search_fn_name)
    except KeyError:
        raise HTTPException(
            status_code=422,
            detail='Ranking function "{search_fn_name}" doesn\'t exist!!!',
        )

    global_params = Params()
    global_params.register(get_pipeline_param_defaults(search_fn_name))
    query.populate_params(global_params)

    rank_pipeline = get_pipeline(search_fn_name)
    search_results: SearchResults = await rank_pipeline(query, global_params)
    search_results.debug_info = DebugInfo(query=query)

    # TODO: Remove this hack once UI is more flexible about names/descriptions.
    search_results.results_data[:] = [
        _rewrite_doc_content(doc) for doc in search_results.results_data
    ]

    return search_results


class SearchFlow(BaseModel):
    name: str
    params: dict


class SearchMetadata(BaseModel):
    search_flows: list[SearchFlow]


@app.post("/search_metadata")
async def search_metadata() -> SearchMetadata:
    return SearchMetadata(
        search_flows=[
            SearchFlow(
                name=search_fn_name, params=get_pipeline_param_defaults(search_fn_name)
            )
            for search_fn_name in list_pipelines()
        ]
    )
