import uvicorn
import os
import loggers
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from logging import getLogger
from dotenv import load_dotenv
from os import getenv
from fastapi import Request
from app.oauth import oauth_router
from app.registeration import registeration_routes
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db, init_users, init_teams, init_lobbies

from slowapi import _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.limitting import limiter 

load_dotenv()

logger = getLogger(__name__)

# Load environment variables
SECRET_KEY = getenv("SESSION_SECRET_KEY")
IS_DEV = getenv("IS_DEV", "false").lower() == "true"  # Convert to boolean
SECURE_LOGIN = getenv("SECURE_LOGIN")

assert SECRET_KEY is not None, "SESSION_SECRET_KEY not found in environment."



# Lifespan context
@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await init_users()
    await init_teams()
    await init_lobbies()

    from app.database import users, teams, lobbies

    app.state.users = users
    app.state.teams = teams
    app.state.lobbies = lobbies

    yield

# FastAPI app
app = FastAPI(debug=True, lifespan=lifespan)

# Session middleware
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://obscura.ccstiet.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting setup
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Debug middleware (optional)
@app.middleware("http")
async def debug_middleware(request, call_next):
    response = await call_next(request)
    return response

# Include routers
app.include_router(oauth_router)
app.include_router(registeration_routes)
# app.include_router(admin_routes)

# Test route
@app.get("/test")
async def test(request:Request):
    return {"message": "backend is up and running!"}

# Run the app
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=3021, reload=IS_DEV)
