from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.metadata_routes import router as metadata_router

# Import API routers
from api.query_routes import router as query_router
from api.static_routes import setup_static_routes

def create_app():
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Document Q&A API",
        description="API for uploading and querying documents with LLM",
        version="1.0.0"
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(query_router)
    app.include_router(metadata_router)


    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy"}

    setup_static_routes(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    import os
    from src.utils.helper import ensure_temp_directory
    
    ensure_temp_directory()
    
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)