# app/schemas.py - Request and response models for FastAPI endpoints.

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field('ok', description='Status kesehatan API')
    service: str = Field('nlp-zahir-api', description='Nama layanan backend')
    version: str = Field('1.0.0', description='Versi API')


class UploadResponse(BaseModel):
    success: bool = Field(True, description='Status keberhasilan upload')
    session_id: str = Field(..., description='Identifier unik sesi ingestion')
    message: str = Field(..., description='Pesan deskriptif hasil upload')
    metadata: Dict[str, Any] = Field(default_factory=dict, description='Metadata aktual hasil ingestion')


class AnalyzeRequest(BaseModel):
    session_id: Optional[str] = Field(None, description='Identifier sesi ingestion yang akan dianalisis')


class ErrorDetail(BaseModel):
    code: str = Field(..., description='Kode error sistem')
    message: str = Field(..., description='Deskripsi pesan error')


class AnalyzeResponse(BaseModel):
    success: bool = Field(..., description='Status keberhasilan analisis')
    session_id: str = Field(..., description='Identifier sesi ingestion')
    status: str = Field(..., description='Status eksekusi pipeline (completed/failed)')
    message: Optional[str] = Field(None, description='Pesan deskriptif hasil analisis')
    error: Optional[ErrorDetail] = Field(None, description='Detail error jika analisis gagal')

class TopIssueSchema(BaseModel):
    category: str
    count: int


class CategoryDistItemSchema(BaseModel):
    category: str
    count: int
    percentage: float


class AnalysisPeriodSchema(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


class DatasetSchema(BaseModel):
    type: str
    session_id: Optional[str] = None


class OverviewResponse(BaseModel):
    session_id: Optional[str] = None
    dataset: DatasetSchema
    total_issues: int
    total_conversations: int
    remote_cases: int
    non_remote_cases: int
    unknown_remote_cases: int
    remote_rate: float
    top_issue: Optional[TopIssueSchema] = None
    category_distribution: list[CategoryDistItemSchema]
    analysis_period: AnalysisPeriodSchema

class IssueCategoryItemSchema(BaseModel):
    category: str
    total_cases: int
    remote_cases: int
    non_remote_cases: int
    unknown_remote_cases: int
    remote_rate: float
    percentage_of_total: float
class IssuesResponse(BaseModel):
    session_id: Optional[str] = None
    dataset: DatasetSchema
    total_issues: int
    categories: list[IssueCategoryItemSchema]

class RemoteCategoryItemSchema(BaseModel):
    category: str
    total_cases: int
    remote_cases: int
    non_remote_cases: int
    unknown_remote_cases: int
    remote_rate: float

class RemoteCustomerItemSchema(BaseModel):
    customer: str
    total_cases: int
    remote_cases: int
    non_remote_cases: int
    unknown_remote_cases: int
    remote_rate: float

class RemoteResponse(BaseModel):
    session_id: Optional[str] = None
    dataset: DatasetSchema
    total_remote: int
    total_non_remote: int
    total_unknown: int
    remote_rate: float
    remote_by_category: list[RemoteCategoryItemSchema]
    remote_by_customer: list[RemoteCustomerItemSchema]

class CustomerItemSchema(BaseModel):
    customer: str
    total_issues: int
    total_remote: int
    total_non_remote: int
    total_unknown: int
    remote_rate: float
    top_issue: str

class CustomerResponse(BaseModel):
    session_id: Optional[str] = None
    dataset: DatasetSchema
    total_customers: int
    customers: list[CustomerItemSchema]

class TimeSeriesItemSchema(BaseModel):
    period: str
    total_issues: int
    remote_cases: int
    non_remote_cases: int
    unknown_remote_cases: int
    top_issue: str

class TimeSeriesResponse(BaseModel):
    session_id: Optional[str] = None
    dataset: DatasetSchema
    period: str
    data: list[TimeSeriesItemSchema]
