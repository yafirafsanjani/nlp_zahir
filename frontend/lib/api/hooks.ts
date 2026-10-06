'use client'

import useSWR from 'swr'
import { useDataset } from '@/components/providers/dataset-provider'
import type { Period } from '@/lib/categories'
import { fetchAnalytics, fetchConversations, type ApiKey, type ApiPath, type ConversationsFilter } from './client'
import type {
  CustomersData,
  ConversationsData,
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


export function useConversations(filters?: ConversationsFilter) {
  const { sessionId } = useDataset()
  const key = [
    '/api/conversations',
    sessionId,
    filters?.page ?? 1,
    filters?.pageSize ?? 20,
    filters?.search ?? '',
    filters?.category ?? '',
    filters?.remote ?? '',
    filters?.clientResponse ?? '',
    filters?.match ?? '',
  ] as const

  return useSWR<ConversationsData, Error>(
    key,
    () => fetchConversations(sessionId, filters),
    {
      revalidateOnFocus: false,
      keepPreviousData: true,
    }
  )
}

