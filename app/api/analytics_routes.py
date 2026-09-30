"""REST endpoints for read-only, session-scoped dashboard analytics."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from app.schemas import CustomerResponse, IssuesResponse, OverviewResponse, RemoteResponse, TimeSeriesResponse
from app.services.analytics_service import AnalyticsError, AnalyticsService


router = APIRouter(prefix="/api", tags=["Analytics"])
analytics_service = AnalyticsService()


def _service_result(callable_):
    try:
        return callable_()
    except AnalyticsError as error:
        raise HTTPException(
            status_code=error.status_code,
            detail={"code": error.code, "message": error.message},
        ) from error


@router.get("/overview", response_model=OverviewResponse)
def get_overview(
    session_id: Optional[str] = Query(None, min_length=1),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    return _service_result(lambda: analytics_service.overview(session_id, start_date, end_date))


@router.get("/issues", response_model=IssuesResponse)
def get_issues(
    session_id: Optional[str] = Query(None, min_length=1),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    return _service_result(lambda: analytics_service.issues(session_id, start_date, end_date))


@router.get("/remote", response_model=RemoteResponse)
def get_remote(
    session_id: Optional[str] = Query(None, min_length=1),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    return _service_result(lambda: analytics_service.remote(session_id, start_date, end_date))


@router.get("/customers", response_model=CustomerResponse)
def get_customers(
    session_id: Optional[str] = Query(None, min_length=1),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    return _service_result(lambda: analytics_service.customers(session_id, start_date, end_date))


@router.get("/time-series", response_model=TimeSeriesResponse)
def get_time_series(
    session_id: Optional[str] = Query(None, min_length=1),
    period: str = Query("monthly", pattern="^(daily|weekly|monthly|yearly)$"),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    return _service_result(lambda: analytics_service.time_series(session_id, period, start_date, end_date))
