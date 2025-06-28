'''FastAPI application for test_substrate_project.'''

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from . import __version__

app = FastAPI(
    title="test_substrate_project",
    description="API for test_substrate_project",
    version=__version__,
)


@app.get("/")
async def root():
    '''Root endpoint.'''
    return {"message": "Hello from test_substrate_project!", "version": __version__}


@app.get("/health")
async def health():
    '''Health check endpoint.'''
    return JSONResponse(
        status_code=200,
        content={"status": "healthy", "version": __version__}
    )