from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import Base, engine
from app.routes import alerts, budget, teams, usage


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="InfraTrack API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(teams, prefix="/api", tags=["teams"])
app.include_router(usage, prefix="/api", tags=["usage"])
app.include_router(alerts, prefix="/api", tags=["alerts"])
app.include_router(budget, prefix="/api", tags=["budget"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
