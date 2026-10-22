from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI(
    title="LegalEase API",
    description="AI-assisted legal document drafting API. Outputs are drafts, not legal advice.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.include_router(router)

@app.get("/")
def home():
    return {"app": "LegalEase", "status": "ok", "docs": "/docs"}

@app.get("/health")
def health():
    return {"status": "ok"}
