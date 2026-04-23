import time
import uuid

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware


def register_middleware(app: FastAPI):

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        process_time = time.perf_counter() - start
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        return response

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        print(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        print(f"Response status: {response.status_code}")
        return response

    @app.middleware("http")
    async def add_request_id_header(request: Request, call_next):
        request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response

    # Bloqueador de IPs (ejemplo simple)
    @app.middleware("http")
    async def block_ip_middleware(request: Request, call_next):
        blocked_ips = {}  # Ejemplo de IP bloqueada
        client_ip = request.client.host
        if client_ip in blocked_ips:
            return Response(
                content="Access Forbidden", status_code=status.HTTP_403_FORBIDDEN
            )
        return await call_next(request)
