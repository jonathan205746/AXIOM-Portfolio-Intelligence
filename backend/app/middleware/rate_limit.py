"""Rate limiting middleware."""

import time
from collections import defaultdict
from typing import Callable, Dict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60, auth_requests_per_minute: int = 10):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.auth_requests_per_minute = auth_requests_per_minute
        self.requests: Dict[str, list] = defaultdict(list)
        self.auth_requests: Dict[str, list] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _is_auth_endpoint(self, path: str) -> bool:
        auth_paths = ["/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth/password-reset"]
        return any(path.startswith(p) for p in auth_paths)

    def _clean_old_requests(self, requests: list, window: int = 60) -> list:
        now = time.time()
        return [req_time for req_time in requests if now - req_time < window]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not request.url.path.startswith("/api/v1"):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()

        if self._is_auth_endpoint(request.url.path):
            self.auth_requests[client_ip] = self._clean_old_requests(self.auth_requests[client_ip])
            if len(self.auth_requests[client_ip]) >= self.auth_requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many authentication requests. Please try again later."},
                    headers={"Retry-After": "60"},
                )
            self.auth_requests[client_ip].append(now)
        else:
            self.requests[client_ip] = self._clean_old_requests(self.requests[client_ip])
            if len(self.requests[client_ip]) >= self.requests_per_minute:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded. Please slow down."},
                    headers={"Retry-After": "60"},
                )
            self.requests[client_ip].append(now)

        return await call_next(request)