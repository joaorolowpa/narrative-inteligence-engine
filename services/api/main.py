from fastapi import FastAPI

from core.schemas import HealthResponse

app = FastAPI(title="Narrative Intelligence API")


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")
