from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

router = APIRouter(tags=["Static Content"])

@router.get("/", response_class=FileResponse)
async def get_index():
    """Serve the main index.html file"""
    return FileResponse("client/index.html")

def setup_static_routes(app: FastAPI):
    """Set up routes for serving static content"""
    # Mount static files from the client directory
    app.mount("/static", StaticFiles(directory="client"), name="static")
    
    # Include the router with the index route
    app.include_router(router)