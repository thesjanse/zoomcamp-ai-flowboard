from fastapi import APIRouter

from ..models import HealthStatus

router = APIRouter(tags=["health"])


@router.get("/healthz", response_model=HealthStatus)
def health_check() -> HealthStatus:
    return HealthStatus(status="ok")