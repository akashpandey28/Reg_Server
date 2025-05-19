from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from src.api.query_routes import router as query_router
from src.api.static_routes import setup_static_routes

def create_app():
    """Create and configure the FastAPI application"""
    # Create FastAPI application
    app = FastAPI(
        title="Document Q&A API",
        description="API for uploading and querying documents with LLM",
        version="1.0.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register API routers
    app.include_router(query_router)
    
    # Add missing routers if they exist in your project
    # Uncomment as needed:
    # from src.api.document_routes import router as document_router
    # from src.api.metadata_routes import router as metadata_router
    # app.include_router(document_router)
    # app.include_router(metadata_router)

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        return {"status": "healthy"}
    
    # Setup static file serving
    setup_static_routes(app)
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    import os
    from src.utils.helper import ensure_temp_directory
    
    # Ensure temp directory exists
    ensure_temp_directory()
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", "8000"))
    
    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)