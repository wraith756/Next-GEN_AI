import asyncio
import threading
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import auth, sessions, settings
from backend.api.ws import router as ws_router, set_event_loop, on_wake
from backend.db.database import init_db
from backend.engine import hotword


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    loop = asyncio.get_event_loop()
    set_event_loop(loop)
    hotword.register_callback(on_wake)
    hw_thread = threading.Thread(target=hotword.start, daemon=True)
    hw_thread.start()
    yield
    hotword.stop()


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(auth.router)
app.include_router(sessions.router)
app.include_router(settings.router)
