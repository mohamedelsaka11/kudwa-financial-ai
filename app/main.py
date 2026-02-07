
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api.routes import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    
    print("\n" + "=" * 50)
    print("Kudwa Financial AI Starting...")
    print("=" * 50)
    init_db()
    print("Ready to serve requests!")
    print("Docs: http://localhost:8000/docs")
    print("=" * 50 + "\n")
    
    yield  
    
   
    print("\n" + "=" * 50)
    print("Kudwa Financial AI Shutting down...")
    print("=" * 50 + "\n")


app = FastAPI(
    title="Kudwa Financial AI",
    description="AI-powered financial data processing and natural language querying system",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router, prefix="/api/v1", tags=["Financial Data"])


@app.get("/")
def root():
    return {
        "name": "Kudwa Financial AI",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "api": "/api/v1"
    }