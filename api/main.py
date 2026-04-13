from dotenv import load_dotenv
load_dotenv(override=True)

import os
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from api.limiter import limiter
from api.routers import auth, chat, documents, users

app = FastAPI(title="AI Avatar Platform")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Dashboard routes locked to Amplify origin; /chat gets its own CORS override below
DASHBOARD_ORIGINS = os.getenv(
    "DASHBOARD_ORIGINS",
    "http://localhost:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=DASHBOARD_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def cors_open_for_chat(request: Request, call_next):
    response: Response = await call_next(request)
    if request.url.path == "/chat":
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(users.router)

@app.get("/health")
def health():
    return {"status": "ok"}

