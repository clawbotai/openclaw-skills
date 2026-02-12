"""MPMP — Medical Practice Management Platform entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.auth import router as auth_router
from app.api.v1.patients import router as patients_router
from app.api.v1.clinical import router as clinical_router
from app.api.v1.appointments import router as appointments_router
from app.api.v1.billing import router as billing_router
from app.api.v1.calculator import router as calculator_router
from app.api.v1.webhooks import router as webhooks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(patients_router, prefix="/api/v1")
app.include_router(clinical_router, prefix="/api/v1")
app.include_router(appointments_router, prefix="/api/v1")
app.include_router(billing_router, prefix="/api/v1")
app.include_router(calculator_router, prefix="/api/v1")
app.include_router(webhooks_router, prefix="/api/v1")


# WebSocket manager for real-time inventory updates
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                pass


ws_manager = ConnectionManager()


@app.websocket("/ws/inventory")
async def inventory_ws(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": settings.APP_VERSION,
        "azoth_sync": settings.AZOTH_OS_SYNC,
    }
