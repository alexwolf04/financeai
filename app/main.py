from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn

from app.api import transactions, predictions, recommendations, dashboard
from app.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="FinanceAI API",
    description="AI-powered personal finance advisor",
    version="1.0.0"
)

# CORS middleware - restrict origins in production
import os
from dotenv import load_dotenv

load_dotenv()

allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers
app.include_router(transactions.router, prefix="/api/transactions", tags=["transactions"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(recommendations.router, prefix="/api/recommendations", tags=["recommendations"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])

@app.get("/")
async def root():
    return {"message": "FinanceAI API - Intelligent Personal Finance Advisor"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "FinanceAI"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)