from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import language, intent, sentiment, analyze

app = FastAPI(
    title="Social Commerce Comment Interpreter",
    description="Rule-based multilingual comment analysis for social media sellers",
    version="1.0.0"
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

@app.get("/")
def root():
    return {
        "status": "running",
        "message": "Comment Interpreter API is live"
    }