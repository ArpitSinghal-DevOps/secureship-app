"""SecureShip sample service: a small FastAPI app shipped through a secure supply chain."""

import os
import time

from fastapi import FastAPI, Request, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

APP_VERSION = os.getenv("APP_VERSION", "dev")

# Interactive docs are disabled: they load third-party JS and widen the attack surface.
app = FastAPI(title="SecureShip", docs_url=None, redoc_url=None, openapi_url=None)

REQUESTS = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "path", "status"]
)
LATENCY = Histogram(
    "http_request_duration_seconds", "HTTP request latency in seconds", ["method", "path"]
)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "geolocation=(), camera=(), microphone=()",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
}

KNOWN_PATHS = {"/", "/health", "/metrics"}


@app.middleware("http")
async def observe_and_harden(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    # Collapse unknown paths into one label so scanners cannot explode metric cardinality.
    path = request.url.path if request.url.path in KNOWN_PATHS else "other"
    LATENCY.labels(request.method, path).observe(time.perf_counter() - start)
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    response.headers.update(SECURITY_HEADERS)
    return response


@app.get("/")
def root():
    return {"service": "secureship", "version": APP_VERSION, "supply_chain": "scanned, signed, verified"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
