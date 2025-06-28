'''FastAPI application for container_demo.'''

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import __version__

app = FastAPI(
    title="container_demo",
    description="API for container_demo",
    version=__version__,
)


@app.get("/")
async def root():
    '''Root endpoint.'''
    return {"message": "Hello from container_demo!", "version": __version__}


@app.get("/health")
async def health():
    '''Health check endpoint.'''
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "version": __version__}
    )