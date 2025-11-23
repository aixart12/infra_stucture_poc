from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import time
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="FastAPI GitOps Demo", version="1.0.0")

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start_time = time.time()
    method = request.method
    path = request.url.path
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    status_code = response.status_code
    
    logger.info(f"{method} {path} - {status_code} - {duration:.3f}s")
    
    return response

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {
        "message": "Welcome to FastAPI GitOps Demo",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.get("/health")
async def health():
    """Health check endpoint for Kubernetes"""
    return {"status": "healthy", "service": "fastapi-demo"}

@app.get("/ready")
async def ready():
    """Readiness check endpoint for Kubernetes"""
    return {"status": "ready", "service": "fastapi-demo"}

@app.get("/api/items")
async def get_items():
    """Demo endpoint that returns sample data"""
    logger.info("Items endpoint accessed")
    return {
        "items": [
            {"id": 1, "name": "Item 1", "description": "First item"},
            {"id": 2, "name": "Item 2", "description": "Second item"},
            {"id": 3, "name": "Item 3", "description": "Third item"}
        ]
    }

@app.get("/api/status")
async def status():
    """Status endpoint with application info"""
    return {
        "app": "fastapi-demo",
        "version": "1.0.0",
        "status": "running",
        "environment": os.getenv("ENVIRONMENT", "development")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

