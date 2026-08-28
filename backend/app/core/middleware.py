import time
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import structlog

logger = structlog.get_logger()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # Add request ID to headers for tracing
        request.state.request_id = request_id
        
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(process_time * 1000, 2),
            )
            
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration_ms=round(process_time * 1000, 2),
            )
            raise


class CORSMiddleware:
    def __init__(self, app, allow_origins=None, allow_methods=None, allow_headers=None):
        self.app = app
        self.allow_origins = allow_origins or ["*"]
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        headers = dict(scope.get("headers", []))
        origin = headers.get(b"origin", b"").decode()
        
        async def send_with_cors(message):
            if message["type"] == "http.response.start":
                response_headers = list(message.get("headers", []))
                response_headers.extend([
                    (b"access-control-allow-origin", origin.encode() if origin in self.allow_origins or "*" in self.allow_origins else b""),
                    (b"access-control-allow-credentials", b"true"),
                    (b"access-control-allow-methods", b", ".join(m.encode() for m in self.allow_methods)),
                    (b"access-control-allow-headers", b", ".join(h.encode() for h in self.allow_headers)),
                ])
                message["headers"] = response_headers
            await send(message)
        
        await self.app(scope, receive, send_with_cors)