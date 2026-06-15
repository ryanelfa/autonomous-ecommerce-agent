"""FastAPI entrypoint: GraphQL + WebSocket + simulator + agent worker."""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from .agent.core import Agent, agent_worker, build_registry
from .bus import agent_queue, bus
from .db import init_db
from .graphql_schema import schema
from .simulator import simulator_loop
from .ws import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    agent = Agent(registry=build_registry(), bus=bus)
    tasks = [
        asyncio.create_task(simulator_loop()),
        asyncio.create_task(agent_worker(agent, agent_queue)),
    ]
    yield
    for task in tasks:
        task.cancel()


app = FastAPI(title="Agent War Room", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(ws_router)
app.include_router(GraphQLRouter(schema), prefix="/graphql")


@app.get("/health")
def health() -> dict:
    return {"ok": True}
