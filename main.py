from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time

EMAIL = "23f3001519@ds.study.iitm.ac.in"

ALLOWED_ORIGINS = [
    "https://app-pq2m3a.example.com",
    # Add the exam page origin here if it is different.
    # For example:
    # "https://exam.example.com"
]

RATE_LIMIT = 10
WINDOW = 10  # seconds

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Per-client request history
client_hits = {}


@app.middleware("http")
async def request_context_and_rate_limit(request: Request, call_next):

    # ---------- Request ID ----------
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id

    # ---------- Rate limiting ----------
    client = request.headers.get("X-Client-Id", "default")
    now = time.time()

    hits = client_hits.setdefault(client, [])

    # Remove expired timestamps
    hits[:] = [t for t in hits if now - t < WINDOW]

    if len(hits) >= RATE_LIMIT:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded"},
            headers={"X-Request-ID": request_id},
        )

    hits.append(now)

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    return response


@app.get("/ping")
def ping(request: Request):
    return {
        "email": EMAIL,
        "request_id": request.state.request_id,
    }