'use client'

import { useState } from 'react'
import { CalendarClock, CalendarDays, Sigma, TrendingUp } from 'lucide-react'
import { PageHeader } from '@/components/analytics/page-header'
import { KpiRow, type Kpi } from '@/components/analytics/kpi-row'
import { Panel, CategoryName } from '@/components/analytics/panel'
import { HandlingLegend } from '@/components/analytics/handling-split'
import { HandlingStackedChart, VolumeAreaChart } from '@/components/analytics/time-charts'
import { PeriodSelector } from '@/components/analytics/filters'
import { DataTable, type Column } from '@/components/analytics/data-table'
import { ChartSkeleton, EmptyState, ErrorState, TableSkeleton } from '@/components/analytics/states'
import { useTimeSeries } from '@/lib/api/hooks'
import type { TimePoint } from '@/lib/api/types'
import { PERIOD_LABELS, type Period } from '@/lib/categories'
import { formatDecimal, formatNumber, formatPercent } from '@/lib/format'

const PERIOD_NOUN: Record<Period, string> = { daily: 'day', weekly: 'week', monthly: 'month', yearly: 'year' }

function buildKpis(points: TimePoint[], period: Period): Kpi[] {
  const total = points.reduce((s, p) => s + p.total, 0)
  const peak = points.reduce((best, p) => (p.total > best.total ? p : best), points[0])
  const latest = points[points.length - 1]
  const previous = points[points.length - 2]
  const change = previous && previous.total ? (latest.total - previous.total) / previous.total : null
  const noun = PERIOD_NOUN[period]
  return [
    {
      label: 'Issues in Range',
      value: formatNumber(total),
      context: `${points.length} ${noun}${points.length === 1 ? '' : 's'} shown`,
      icon: Sigma,
    },
    {
      label: `Average per ${noun}`,
      value: formatDecimal(points.length ? total / points.length : 0),
      context: `${PERIOD_LABELS[period]} average`,
      icon: CalendarDays,
    },
    {
      label: 'Peak Period',
      value: peak.full_label,
      context: `${formatNumber(peak.total)} issues`,
      icon: TrendingUp,
      textValue: true,
    },
    {
      label: `Latest ${noun}`,
      value: formatNumber(latest.total),
      context:
        change === null
          ? latest.full_label
          : `${change >= 0 ? '+' : ''}${formatPercent(change)} vs previous ${noun}`,
      icon: CalendarClock,
      emphasis: true,
    },
  ]
}

const columns: Column<TimePoint>[] = [
  {
    key: 'period',
    header: 'Period',
    sortValue: (r) => r.start,
    cell: (r) => <span className="font-medium whitespace-nowrap text-foreground">{r.full_label}</span>,
  },
  { key: 'total', header: 'Total Issues', align: 'right', sortValue: (r) => r.total, cell: (r) => formatNumber(r.total) },
  { key: 'remote', header: 'Remote', align: 'right', sortValue: (r) => r.remote, cell: (r) => formatNumber(r.remote) },
  {
    key: 'non_remote',
    header: 'Non-Remote',
    align: 'right',
    sortValue: (r) => r.non_remote,
    cell: (r) => formatNumber(r.non_remote),
  },
  {
    key: 'remote_rate',
    header: 'Remote Rate',
    align: 'right',
    sortValue: (r) => (r.remote + r.non_remote ? r.remote / (r.remote + r.non_remote) : 0),
    cell: (r) => formatPercent(r.remote + r.non_remote ? r.remote / (r.remote + r.non_remote) : 0),
  },
  {
    key: 'top_issue',
    header: 'Top Issue',
    sortValue: (r) => r.top_issue ?? '',
    cell: (r) => (r.top_issue ? <CategoryName value={r.top_issue} className="font-normal" /> : '—'),
  },
]

export function TimeView() {
  const [period, setPeriod] = useState<Period>('monthly')
  const series = useTimeSeries(period)
  const points = series.data?.points
  const hasData = points && points.some((p) => p.total > 0)

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Time Analysis" description="Support volume and handling method across time periods." />

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <span id="time-period-label" className="text-xs font-medium text-muted-foreground">
          Period
        </span>
        <PeriodSelector value={period} onChange={setPeriod} label="Time analysis period" />
      </div>

      {series.error ? (
        <ErrorState onRetry={() => series.mutate()} />
      ) : points && !hasData ? (
        <div className="rounded-lg border bg-card">
          <EmptyState message="No issues were recorded in the selected period." />
        </div>
      ) : (
        <>
          <KpiRow items={points ? buildKpis(points, period) : null} loading={!points} />

          <Panel title="Issue Volume Over Time" description={`${PERIOD_LABELS[period]} detected issues`}>
            {points ? <VolumeAreaChart points={points} /> : <ChartSkeleton />}
          </Panel>

          <Panel
            title="Handling Method Over Time"
            description="Remote, non-remote and unknown handling per period"
            actions={<HandlingLegend />}
          >
            {points ? <HandlingStackedChart points={points} /> : <ChartSkeleton />}
          </Panel>

          <Panel title="Period Summary" description="Aggregated counts per period" bodyClassName="pt-2">
            {points ? (
              <DataTable
                key={period}
                caption="Period summary"
                columns={columns}
                rows={points}
                rowKey={(r) => r.key}
                initialSort={{ key: 'period', direction: 'desc' }}
              />
            ) : (
              <TableSkeleton columns={6} />
            )}
          </Panel>
        </>
      )}
    </div>
  )
}
