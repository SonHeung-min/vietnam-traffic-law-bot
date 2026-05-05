from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.chat import router as chat_router
from app.api.health import router as health_router

app = FastAPI(
    title="Traffic Law Chatbot API",
    description="API cho chatbot hỏi đáp Luật Giao thông Đường bộ Việt Nam",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "message": "Traffic Law Chatbot API",
        "docs": "/docs",
        "health": "/health",
    }
