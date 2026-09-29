"""Audit logging middleware."""

import json
import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("audit")


class AuditLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, exclude_paths: list[str] | None = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json", "/redoc"]

    def _should_log(self, path: str) -> bool:
        return not any(path.startswith(p) for p in self.exclude_paths)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self._should_log(request.url.path):
            return await call_next(request)

        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")
        client_ip = self._get_client_ip(request)
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""

        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.get("id")

        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            audit_log = {
                "request_id": request_id,
                "timestamp": time.time(),
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_ip": client_ip,
                "user_id": user_id,
                "status_code": response.status_code,
                "process_time_ms": round(process_time * 1000, 2),
            }

            if response.status_code >= 400:
                logger.warning("API request failed: %s", json.dumps(audit_log))
            else:
                logger.info("API request: %s", json.dumps(audit_log))

            response.headers["X-Process-Time"] = str(round(process_time * 1000, 2))
            return response
        except Exception as e:
            process_time = time.time() - start_time
            audit_log = {
                "request_id": request_id,
                "timestamp": time.time(),
                "method": method,
                "path": path,
                "query_params": query_params,
                "client_ip": client_ip,
                "user_id": user_id,
                "status_code": 500,
                "process_time_ms": round(process_time * 1000, 2),
                "error": str(e),
            }
            logger.error("API request error: %s", json.dumps(audit_log))
            raise