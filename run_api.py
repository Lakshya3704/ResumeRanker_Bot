"""
run_api.py – Quick-start script for the FastAPI server.

Usage:
    python run_api.py

Starts the API on http://localhost:8000
Swagger docs at http://localhost:8000/docs
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
