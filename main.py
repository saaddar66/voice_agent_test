from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import traceback
import logging

from routers.patients import router as patients_router
from routers.vapi import router as vapi_router
from database import Base, engine

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize the database tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="Patient Registration System", lifespan=lifespan)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {
        "data": {
            "message": "Welcome to the Patient Registration System API",
            "docs": "/docs",
            "status": "online"
        },
        "error": None
    }

app.include_router(patients_router)
app.include_router(vapi_router)

# Serve the static frontend dashboard
app.mount("/dashboard", StaticFiles(directory="frontend", html=True), name="frontend")

# Exception handlers for standard envelope format
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"data": None, "error": str(exc.detail)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    error_msgs = []
    for err in errors:
        loc = ".".join([str(l) for l in err.get("loc", [])])
        error_msgs.append(f"{loc}: {err.get('msg')}")
    
    error_msg = "; ".join(error_msgs) if error_msgs else "Validation error"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"data": None, "error": error_msg}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logging.error(f"Internal server error: {exc}")
    logging.error(traceback.format_exc())
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"data": None, "error": "Internal server error"}
    )

