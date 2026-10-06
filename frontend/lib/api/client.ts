import { isCategory, type Period } from '@/lib/categories'
import type {
  ConversationsData,
  ConversationsResponse,
  AnalyzeResponse,
  AnalyzeResult,
  ApiCategory,
  CategoryStat,
  CustomersData,
  CustomersResponse,
  IssuesData,
  IssuesResponse,
  OverviewData,
  OverviewResponse,
  RemoteData,
  RemoteResponse,
  TimePoint,
  TimeSeriesData,
  TimeSeriesResponse,
  UploadResponse,
  UploadStep,
} from './types'

/** Public, deployment-specific URL of the FastAPI service (for example https://api.example.com). */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, '')

export type ApiPath = '/api/overview' | '/api/issues' | '/api/remote' | '/api/customers' | '/api/time-series'
export type ApiKey = readonly [path: ApiPath, sessionId: string | null, period?: Period]

export class ApiError extends Error {}
export class UploadError extends ApiError {}

function apiCategory(value: string): ApiCategory {
  return isCategory(value) ? value : 'UNKNOWN_UNCLASSIFIED'
}

function ratio(percent: number): number {
  return percent / 100
}

function categoryStat(item: {
  category: string
  total_cases: number
  remote_cases: number
  non_remote_cases: number
  unknown_remote_cases: number
  remote_rate: number
  percentage_of_total?: number
}): CategoryStat {
  return {
    category: apiCategory(item.category),
    total: item.total_cases,
    remote: item.remote_cases,
    non_remote: item.non_remote_cases,
    unknown: item.unknown_remote_cases,
    remote_rate: ratio(item.remote_rate),
    share: ratio(item.percentage_of_total ?? 0),
  }
}

function formatPeriod(period: string): string {
  const formatter = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
  if (/^\d{4}-\d{2}-\d{2}$/.test(period)) return formatter.format(new Date(`${period}T00:00:00Z`))
  if (/^\d{4}-\d{2}$/.test(period)) return new Intl.DateTimeFormat('en-GB', { month: 'short', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${period}-01T00:00:00Z`))
  return period
}

function overviewData(data: OverviewResponse): OverviewData {
  return {
    total_issues: data.total_issues,
    total_remote: data.remote_cases,
    total_non_remote: data.non_remote_cases,
    total_unknown: data.unknown_remote_cases,
    remote_rate: ratio(data.remote_rate),
    top_issue: data.top_issue
      ? { category: apiCategory(data.top_issue.category), total: data.top_issue.count, share: data.total_issues ? data.top_issue.count / data.total_issues : 0 }
      : null,
    categories: data.category_distribution.map((item) => ({
      category: apiCategory(item.category), total: item.count, share: ratio(item.percentage),
    })),
    date_range: data.analysis_period.start && data.analysis_period.end
      ? { start: data.analysis_period.start, end: data.analysis_period.end }
      : null,
  }
}

function customersData(data: CustomersResponse): CustomersData {
  const customers = data.customers.map((item) => ({
    customer: item.customer,
    total: item.total_issues,
    remote: item.total_remote,
    non_remote: item.total_non_remote,
    unknown: item.total_unknown,
    remote_rate: ratio(item.remote_rate),
    top_issue: apiCategory(item.top_issue),
  }))
  const total_issues = customers.reduce((total, customer) => total + customer.total, 0)
  return {
    total_customers: data.total_customers,
    total_issues,
    avg_issues_per_customer: data.total_customers ? total_issues / data.total_customers : 0,
    customers,
  }
}

function timeSeriesData(data: TimeSeriesResponse): TimeSeriesData {
  const points: TimePoint[] = data.data.map((item) => ({
    key: item.period,
    label: formatPeriod(item.period),
    full_label: formatPeriod(item.period),
    start: item.period,
    total: item.total_issues,
    remote: item.remote_cases,
    non_remote: item.non_remote_cases,
    unknown: item.unknown_remote_cases,
    top_issue: apiCategory(item.top_issue),
  }))
  return { period: data.period, points }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body: unknown = await response.json()
    if (typeof body === 'object' && body !== null && 'detail' in body) {
      const detail = body.detail
      if (typeof detail === 'string') return detail
      if (typeof detail === 'object' && detail !== null && 'message' in detail && typeof detail.message === 'string') return detail.message
    }
  } catch {
    // An intermediary may return non-JSON; the status remains useful.
  }
  return `Request failed with status ${response.status}.`
}

function analyticsUrl([path, sessionId, period]: ApiKey): URL {
  if (!API_BASE_URL) throw new ApiError('Dashboard API is not configured. Set NEXT_PUBLIC_API_BASE_URL and reload the application.')
  const url = new URL(path, API_BASE_URL)
  if (sessionId) url.searchParams.set('session_id', sessionId)
  if (period) url.searchParams.set('period', period)
  return url
}

export async function fetchAnalytics(key: ApiKey): Promise<OverviewData | IssuesData | RemoteData | CustomersData | TimeSeriesData> {
  const response = await fetch(analyticsUrl(key), { headers: { Accept: 'application/json' } })
  if (!response.ok) throw new ApiError(await errorMessage(response))

  switch (key[0]) {
    case '/api/overview':
      return overviewData((await response.json()) as OverviewResponse)
    case '/api/issues': {
      const data = (await response.json()) as IssuesResponse
      return { total_issues: data.total_issues, categories: data.categories.map(categoryStat) }
    }
    case '/api/remote': {
      const data = (await response.json()) as RemoteResponse
      return {
        total_remote: data.total_remote,
        total_non_remote: data.total_non_remote,
        total_unknown: data.total_unknown,
        remote_rate: ratio(data.remote_rate),
        categories: data.remote_by_category.map(categoryStat),
      }
    }
    case '/api/customers':
      return customersData((await response.json()) as CustomersResponse)
    case '/api/time-series':
      return timeSeriesData((await response.json()) as TimeSeriesResponse)
  }
}

export async function uploadAndAnalyze(file: File, onStep: (step: UploadStep) => void): Promise<AnalyzeResult> {
  if (!API_BASE_URL) throw new UploadError('Dashboard API is not configured. Set NEXT_PUBLIC_API_BASE_URL and reload the application.')
  const form = new FormData()
  form.append('file', file)
  onStep('uploading')
  onStep('validating')
  const uploadResponse = await fetch(new URL('/api/upload', API_BASE_URL), { method: 'POST', body: form })
  if (!uploadResponse.ok) throw new UploadError(await errorMessage(uploadResponse))
  const upload = (await uploadResponse.json()) as UploadResponse

  // The backend executes NLP synchronously; completion is only reported after its request resolves.
  onStep('processing')
  onStep('nlp')
  const analyzeResponse = await fetch(new URL('/api/analyze', API_BASE_URL), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: upload.session_id }),
  })
  if (!analyzeResponse.ok) throw new UploadError(await errorMessage(analyzeResponse))
  const analysis = (await analyzeResponse.json()) as AnalyzeResponse
  if (!analysis.success || analysis.status !== 'completed') {
    throw new UploadError(analysis.error?.message ?? analysis.message ?? 'Analysis could not be completed.')
  }
  onStep('updating')
  onStep('completed')
  return { session_id: analysis.session_id, status: analysis.status, message: analysis.message }
}


export type ConversationsFilter = {
  page?: number
  pageSize?: number
  search?: string
  category?: string
  remote?: string
  clientResponse?: string
  match?: string
}

export async function fetchConversations(
  sessionId: string | null,
  filters?: ConversationsFilter
): Promise<ConversationsData> {
  const base = API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000')
  const url = new URL('/api/conversations', base)
  if (sessionId) url.searchParams.set('session_id', sessionId)
  if (filters?.page) url.searchParams.set('page', String(filters.page))
  if (filters?.pageSize) url.searchParams.set('page_size', String(filters.pageSize))
  if (filters?.search) url.searchParams.set('search', filters.search)
  if (filters?.category) url.searchParams.set('category', filters.category)
  if (filters?.remote) url.searchParams.set('remote', filters.remote)
  if (filters?.clientResponse) url.searchParams.set('client_response', filters.clientResponse)
  if (filters?.match) url.searchParams.set('match', filters.match)

  const response = await fetch(url, { headers: { Accept: 'application/json' } })
  if (!response.ok) throw new ApiError(await errorMessage(response))
  return (await response.json()) as ConversationsData
}

export function getDownloadUrl(sessionId: string | null, format: 'csv' | 'xlsx' = 'csv'): string {
  const base = API_BASE_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000')
  const url = new URL('/api/conversations/download', base)
  if (sessionId) url.searchParams.set('session_id', sessionId)
  url.searchParams.set('format', format)
  return url.toString()
}

