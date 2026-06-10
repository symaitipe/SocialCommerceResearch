from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import language, intent, sentiment, analyze, comments, posts
from app.database import init_db
import asyncio
import sys

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    print("Database initialized")
    yield

app = FastAPI(
    title="Social Commerce Comment Interpreter",
    description="Rule-based multilingual comment analysis for social media sellers",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(language.router)
app.include_router(intent.router)
app.include_router(sentiment.router)
app.include_router(analyze.router)
app.include_router(comments.router)
app.include_router(posts.router)

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Comment Interpreter API is live"
    }