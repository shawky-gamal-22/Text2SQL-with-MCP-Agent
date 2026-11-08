from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from src.text2sql.agent_factory import AgentFactory
from src.services.chat_service import ChatService
from src.api.routes.chat import router as chat_router
from src.api.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    async with AgentFactory.create_agent() as agent:
        app.state.chat_service = ChatService(agent)
        yield


app = FastAPI(
    title="Text2SQL API",
    description="Convert natural-language questions into database answers.",
    lifespan=lifespan,
)
app.include_router(health_router, prefix="/api")
app.include_router(chat_router, prefix="/api")