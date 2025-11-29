"""FastAPI entrypoint with GraphQL endpoint."""
from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.utils import get_openapi
from strawberry.fastapi import GraphQLRouter
import logging

from app.database import connect_to_mongo, close_mongo_connection
from app.graphql_schema import schema
from app.middleware import RateLimitMiddleware, SecurityHeadersMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from app.auth_router import router as auth_router
from app.twilio_webhook import router as twilio_router
from app.notify_router import router as notify_router
from app.camps_router import router as camps_router
from app.volunteers_router import router as volunteers_router
from app.assignments_router import router as assignments_router
from app.activity_router import router as activity_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup
    await connect_to_mongo()
    yield
    # Shutdown
    await close_mongo_connection()


app = FastAPI(
    title="Agentic Volunteer Coordinator API",
    description="Backend API for medical camp volunteer coordination",
    version="0.1.0",
    lifespan=lifespan,
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": False,
        "clientId": "swagger-ui",
    },
    swagger_ui_oauth2_redirect_url="/docs/oauth2-redirect",
)


def custom_openapi() -> Dict[str, Any]:
    """Custom OpenAPI schema with proper OAuth2 configuration for Swagger UI."""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Add OAuth2 security scheme for Swagger UI
    # Use /auth/token endpoint which accepts form data (OAuth2 password flow compatible)
    openapi_schema["components"]["securitySchemes"] = {
        "OAuth2PasswordBearer": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/auth/token",
                    "scopes": {}
                }
            },
            "description": "Login with email (as username) and password to get access token. Use /auth/login for JSON-based login."
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Security and rate limiting middleware
# Rate limiting: 60 requests per minute per IP (configurable via env)
import os
rate_limit = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
app.add_middleware(RateLimitMiddleware, requests_per_minute=rate_limit)
app.add_middleware(SecurityHeadersMiddleware)

# CORS configuration (production-ready)
allowed_origins = os.getenv("CORS_ORIGINS", "").split(",") if os.getenv("CORS_ORIGINS") else []
# In development, allow localhost if no origins specified
if not allowed_origins or allowed_origins == [""]:
    allowed_origins = ["http://localhost:3000", "http://localhost:8000"]  # Dev defaults

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Global exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors with detailed error messages.
    """
    logger.error(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Handle all unhandled exceptions with generic error response.
    
    Logs the full exception for debugging while returning a safe message to the client.
    """
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error. Please try again later."
        }
    )


# Mount GraphQL endpoint
# GET /graphql - Serves GraphQL UI/Playground
# POST /graphql - Standard GraphQL endpoint (query + variables)
graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")

# Mount authentication router
app.include_router(auth_router, prefix="/auth", tags=["auth"])

# Mount Twilio webhook router
app.include_router(twilio_router, prefix="/twilio", tags=["twilio"])

# Mount notification router
app.include_router(notify_router, prefix="/notify", tags=["notifications"])

# Mount REST CRUD routers
app.include_router(camps_router, prefix="/api/camps", tags=["camps"])
app.include_router(volunteers_router, prefix="/api/volunteers", tags=["volunteers"])
app.include_router(assignments_router, prefix="/api/assignments", tags=["assignments"])
app.include_router(activity_router, prefix="/api/activity", tags=["activity"])


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Simple endpoint that returns server status without accessing the database.
    Used for monitoring and load balancer health checks.
    
    Returns:
        JSON response: {"status": "ok"}
        
    Status Code:
        200 OK
    """
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

