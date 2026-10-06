"""REST endpoints for read-only, session-scoped dashboard analytics."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from fastapi.responses import FileResponse
from app.schemas import CustomerResponse, IssuesResponse, OverviewResponse, RemoteResponse, TimeSeriesResponse, ConversationsResponse
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


@router.get("/conversations", response_model=ConversationsResponse)
def get_conversations(
    session_id: Optional[str] = Query(None, min_length=1),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    remote: Optional[str] = Query(None),
    client_response: Optional[str] = Query(None),
    match: Optional[str] = Query(None),
):
    return _service_result(
        lambda: analytics_service.conversations(
            session_id=session_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            page_size=page_size,
            search=search,
            category=category,
            remote=remote,
            client_response=client_response,
            match=match,
        )
    )


@router.get("/conversations/download")
def download_conversations(
    session_id: Optional[str] = Query(None, min_length=1),
    format: str = Query("csv", pattern="^(csv|xlsx)$"),
):
    def _download():
        if session_id:
            session_dir = analytics_service._session_dir(session_id)
            target = session_dir / "output" / f"master_conversations_final.{format}"
        else:
            target = analytics_service.default_master_path.with_suffix(f".{format}")

        if not target.is_file():
            if format == "xlsx":
                target = target.with_suffix(".csv")
            if not target.is_file():
                raise AnalyticsError(404, "FILE_NOT_FOUND", "File master data tidak ditemukan.")

        media_type = "text/csv" if target.suffix == ".csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        return FileResponse(
            path=str(target),
            filename=target.name,
            media_type=media_type,
        )

    return _service_result(_download)

