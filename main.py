from contextlib import asynccontextmanager
from fastapi import FastAPI
import uvicorn
import asyncio
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from core.database import engine, Base
from core.config import settings
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from routers import routes
from service.nats_client import nats_client
from service.background_tasks import update_products_task
from service.websocket_manager import manager
import json

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENV in ["development", "production"]:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Database tables created")

    await nats_client.connect()

    async def message_handler(msg):
        subject = msg.subject
        data = msg.data.decode()
        print(f"NATS message received [{subject}]: {data}")

        try:
            nats_data = json.loads(data)
            await manager.broadcast({
                "type": "nats_event",
                "source": "NATS",
                "subject": subject,
                "data": nats_data
            })
        except Exception as e:
            print(f"Error forwarding NATS to WebSocket: {e}")

    await nats_client.subscribe("items.updates", message_handler)

    task = asyncio.create_task(update_products_task())
    app.state.background_task = task

    yield

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        print("Background task stopped")

    await nats_client.disconnect()

    await engine.dispose()
    print("Database connections closed")


app = FastAPI(
    title="Products Parser API",
    description="REST API + WebSocket + NATS + Background Tasks",
    version="1.0.0",
    lifespan=lifespan,
    debug=settings.DEBUG
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in routes:
    app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Products Parser API",
        "docs": "/docs",
        "frontend(открыть html клиент)": "/monitor",
        "NATS": "http://localhost:8222/"
    }


@app.get("/api/tasks/status")
async def get_background_task_status():
    task_exists = hasattr(app.state, 'background_task')

    if not task_exists:
        return {"status": "not_started"}

    task_running = not app.state.background_task.done()

    return {
        "status": "running" if task_running else "stopped",
        "is_running": task_running
    }


@app.get("/monitor")
async def get_monitor():
    """Открыть monitoring интерфейс"""
    return FileResponse("index.html")

app.mount("/static", StaticFiles(directory="."), name="static")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.APP_HOST,
        port=settings.APP_PORT,
        reload=settings.APP_RELOAD,
        log_level=settings.APP_LOG_LEVEL.lower()
    )
