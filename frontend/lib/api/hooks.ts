'use client'

import useSWR from 'swr'
import { useDataset } from '@/components/providers/dataset-provider'
import type { Period } from '@/lib/categories'
import { fetchAnalytics, type ApiKey, type ApiPath } from './client'
import type {
  CustomersData,
  IssuesData,
  OverviewData,
  RemoteData,
  TimeSeriesData,
} from './types'

function useAnalytics<T>(path: ApiPath, period?: Period) {
  const { sessionId } = useDataset()
  const key: ApiKey = period ? [path, sessionId, period] : [path, sessionId]
  return useSWR<T, Error, ApiKey>(key, (request) => fetchAnalytics(request) as Promise<T>, {
    revalidateOnFocus: false,
    keepPreviousData: true,
  })
}

export const useOverview = () => useAnalytics<OverviewData>('/api/overview')
export const useIssues = () => useAnalytics<IssuesData>('/api/issues')
export const useRemote = () => useAnalytics<RemoteData>('/api/remote')
export const useCustomers = () => useAnalytics<CustomersData>('/api/customers')
export const useTimeSeries = (period: Period) =>
  useAnalytics<TimeSeriesData>('/api/time-series', period)
