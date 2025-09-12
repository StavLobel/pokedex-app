"""
FastAPI main application entry point
"""
from fastapi import FastAPI

app = FastAPI(
    title="Pokemon Image Recognition API",
    description="AI-powered Pokemon identification service",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Pokemon Image Recognition API"}