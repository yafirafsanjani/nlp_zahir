import type { Category, Period } from '@/lib/categories'

/** Mirrors the `dataset` object returned by every FastAPI analytics endpoint. */
export type DatasetInfo = {
  type: 'default' | 'session'
  session_id: string | null
}

export type ApiCategory = Category | 'UNKNOWN_UNCLASSIFIED'
export type DateRange = { start: string; end: string }

// FastAPI response contracts. Percentages here are 0-100, exactly as returned.
export type OverviewResponse = {
  session_id: string | null
  dataset: DatasetInfo
  total_issues: number
  total_conversations: number
  remote_cases: number
  non_remote_cases: number
  unknown_remote_cases: number
  remote_rate: number
  top_issue: { category: string; count: number } | null
  category_distribution: { category: string; count: number; percentage: number }[]
  analysis_period: { start: string | null; end: string | null }
}

export type IssuesResponse = {
  session_id: string | null
  dataset: DatasetInfo
  total_issues: number
  categories: Array<{
    category: string
    total_cases: number
    remote_cases: number
    non_remote_cases: number
    unknown_remote_cases: number
    remote_rate: number
    percentage_of_total: number
  }>
}

export type RemoteResponse = {
  session_id: string | null
  dataset: DatasetInfo
  total_remote: number
  total_non_remote: number
  total_unknown: number
  remote_rate: number
  remote_by_category: Array<{
    category: string
    total_cases: number
    remote_cases: number
    non_remote_cases: number
    unknown_remote_cases: number
    remote_rate: number
  }>
  remote_by_customer: Array<{
    customer: string
    total_cases: number
    remote_cases: number
    non_remote_cases: number
    unknown_remote_cases: number
    remote_rate: number
  }>
}

export type CustomersResponse = {
  session_id: string | null
  dataset: DatasetInfo
  total_customers: number
  customers: Array<{
    customer: string
    total_issues: number
    total_remote: number
    total_non_remote: number
    total_unknown: number
    remote_rate: number
    top_issue: string
  }>
}

export type TimeSeriesResponse = {
  session_id: string | null
  dataset: DatasetInfo
  period: Period
  data: Array<{
    period: string
    total_issues: number
    remote_cases: number
    non_remote_cases: number
    unknown_remote_cases: number
    top_issue: string
  }>
}

export type UploadResponse = {
  success: boolean
  session_id: string
  message: string
  metadata: Record<string, unknown>
}

export type AnalyzeResponse = {
  success: boolean
  session_id: string
  status: 'completed' | 'failed' | string
  message: string | null
  error: { code: string; message: string } | null
}

// UI view models contain only values derived from FastAPI response contracts.
export type CategoryStat = {
  category: ApiCategory
  total: number
  remote: number
  non_remote: number
  unknown: number
  remote_rate: number
  share: number
}

export type OverviewData = {
  total_issues: number
  total_remote: number
  total_non_remote: number
  total_unknown: number
  remote_rate: number
  top_issue: { category: ApiCategory; total: number; share: number } | null
  categories: Array<{ category: ApiCategory; total: number; share: number }>
  date_range: DateRange | null
}

export type IssuesData = { total_issues: number; categories: CategoryStat[] }
export type RemoteData = {
  total_remote: number
  total_non_remote: number
  total_unknown: number
  remote_rate: number
  categories: CategoryStat[]
}

export type CustomerStat = {
  customer: string
  total: number
  remote: number
  non_remote: number
  unknown: number
  remote_rate: number
  top_issue: ApiCategory | null
}

export type CustomersData = {
  total_customers: number
  total_issues: number
  avg_issues_per_customer: number
  customers: CustomerStat[]
}

export type TimePoint = {
  key: string
  label: string
  full_label: string
  start: string
  total: number
  remote: number
  non_remote: number
  unknown: number
  top_issue: ApiCategory | null
}

export type TimeSeriesData = { period: Period; points: TimePoint[] }
export type UploadStep = 'uploading' | 'validating' | 'processing' | 'nlp' | 'updating' | 'completed'
export type AnalyzeResult = { session_id: string; status: string; message: string | null }
