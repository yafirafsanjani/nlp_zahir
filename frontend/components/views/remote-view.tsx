'use client'

import { useState } from 'react'
import { CircleHelp, Gauge, Headset, Wrench } from 'lucide-react'
import { PageHeader } from '@/components/analytics/page-header'
import { KpiRow, type Kpi } from '@/components/analytics/kpi-row'
import { Panel, LegendItem } from '@/components/analytics/panel'
import { HandlingDonut } from '@/components/analytics/handling-donut'
import { HandlingLegend, HandlingSplit } from '@/components/analytics/handling-split'
import { HandlingTrendChart } from '@/components/analytics/time-charts'
import { PeriodSelector } from '@/components/analytics/filters'
import { BarListSkeleton, ChartSkeleton, EmptyState, ErrorState } from '@/components/analytics/states'
import { useRemote, useTimeSeries } from '@/lib/api/hooks'
import type { RemoteData } from '@/lib/api/types'
import type { Period } from '@/lib/categories'
import { HANDLING_COLORS } from '@/lib/chart-colors'
import { formatNumber, formatPercent } from '@/lib/format'

function buildKpis(data: RemoteData): Kpi[] {
  const total = data.total_remote + data.total_non_remote + data.total_unknown
  return [
    {
      label: 'Remote Issues',
      value: formatNumber(data.total_remote),
      context: 'Resolved through remote access',
      icon: Headset,
      emphasis: true,
    },
    {
      label: 'Non-Remote Issues',
      value: formatNumber(data.total_non_remote),
      context: 'Resolved without remote access',
      icon: Wrench,
    },
    {
      label: 'Remote Handling Rate',
      value: formatPercent(data.remote_rate),
      context: `Of ${formatNumber(data.total_remote + data.total_non_remote)} known outcomes`,
      icon: Gauge,
    },
    {
      label: 'Unknown Handling',
      value: formatNumber(data.total_unknown),
      context: `${formatPercent(total ? data.total_unknown / total : 0)} could not be classified`,
      icon: CircleHelp,
    },
  ]
}

export function RemoteView() {
  const remote = useRemote()
  const [period, setPeriod] = useState<Period>('monthly')
  const trend = useTimeSeries(period)
  const data = remote.data

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Remote Analysis"
        description="How issues were resolved and which categories rely most on remote access."
      />

      {remote.error ? (
        <ErrorState onRetry={() => remote.mutate()} />
      ) : (
        <>
          <KpiRow items={data ? buildKpis(data) : null} loading={!data} />
          {data && data.total_remote + data.total_non_remote + data.total_unknown === 0 ? (
            <div className="rounded-lg border bg-card">
              <EmptyState />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
              <Panel title="Handling Method Split" description="Remote vs non-remote resolution" className="lg:col-span-2">
                {data ? (
                  <HandlingDonut remote={data.total_remote} nonRemote={data.total_non_remote} unknown={data.total_unknown} remoteRate={data.remote_rate} />
                ) : (
                  <ChartSkeleton height={200} />
                )}
              </Panel>
              <Panel
                title="Remote Handling by Category"
                description="Sorted by remote handling rate"
                actions={<HandlingLegend />}
                className="lg:col-span-3"
              >
                {data ? <HandlingSplit items={data.categories} sortBy="remote_rate" /> : <BarListSkeleton />}
              </Panel>
            </div>
          )}
        </>
      )}

      <Panel
        title="Remote Handling Trend"
        description="Remote and non-remote issues over time"
        actions={
          <>
            <div className="mr-2 hidden items-center gap-4 md:flex">
              <LegendItem color={HANDLING_COLORS.remote} label="Remote" />
              <LegendItem color={HANDLING_COLORS.non_remote} label="Non-Remote" />
            </div>
            <PeriodSelector value={period} onChange={setPeriod} label="Remote trend period" />
          </>
        }
      >
        {trend.error ? (
          <ErrorState message="The trend data could not be loaded." onRetry={() => trend.mutate()} className="border-0 p-0" />
        ) : trend.data ? (
          <HandlingTrendChart points={trend.data.points} />
        ) : (
          <ChartSkeleton />
        )}
      </Panel>
    </div>
  )
}
