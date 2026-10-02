'use client'

import { useState } from 'react'
import { Award, Headset, Layers, Percent, Wrench } from 'lucide-react'
import { CategoryPerformance } from '@/components/analytics/category-performance'
import { PageHeader } from '@/components/analytics/page-header'
import { KpiRow, type Kpi } from '@/components/analytics/kpi-row'
import { Panel, LegendItem } from '@/components/analytics/panel'
import { CategoryBars } from '@/components/analytics/category-bars'
import { HandlingDonut } from '@/components/analytics/handling-donut'
import { HandlingTrendChart } from '@/components/analytics/time-charts'
import { PeriodSelector } from '@/components/analytics/filters'
import { BarListSkeleton, ChartSkeleton, EmptyState, ErrorState } from '@/components/analytics/states'
import { Skeleton } from '@/components/ui/skeleton'
import { useIssues, useOverview, useTimeSeries } from '@/lib/api/hooks'
import type { CategoryStat, OverviewData, TimePoint } from '@/lib/api/types'
import type { Period } from '@/lib/categories'
import { HANDLING_COLORS } from '@/lib/chart-colors'
import { formatDateRange, formatNumber, formatPercent } from '@/lib/format'

function buildKpis(data: OverviewData): Kpi[] {
  return [
    {
      label: 'Total Issues',
      value: formatNumber(data.total_issues),
      context: formatDateRange(data.date_range),
      icon: Layers,
    },
    {
      label: 'Remote',
      value: formatNumber(data.total_remote),
      context: 'Resolved remotely',
      icon: Headset,
    },
    {
      label: 'Non-Remote',
      value: formatNumber(data.total_non_remote),
      context: `${formatPercent(data.total_issues ? data.total_non_remote / data.total_issues : 0)} of all issues`,
      icon: Wrench,
    },
    {
      label: 'Remote Rate',
      value: formatPercent(data.remote_rate),
      context: `${formatNumber(data.total_remote)} of ${formatNumber(data.total_remote + data.total_non_remote)} known outcomes`,
      icon: Percent,
      emphasis: true,
    },
    {
      label: 'Top Issue',
      value: data.top_issue?.category ?? '—',
      context: data.top_issue
        ? `${formatNumber(data.top_issue.total)} issues · ${formatPercent(data.top_issue.share)}`
        : 'No issues recorded',
      icon: Award,
      textValue: true,
    },
  ]
}

const MIN_SHARE_FOR_RATE = 0.03

function buildInsights(data: OverviewData, categories: CategoryStat[] | undefined, monthly: TimePoint[] | undefined) {
  const insights: { title: string; value: string; detail: string }[] = []
  if (data.top_issue) {
    insights.push({
      title: 'Most Frequent Issue',
      value: data.top_issue.category,
      detail: `${formatNumber(data.top_issue.total)} issues, ${formatPercent(data.top_issue.share)} of total volume.`,
    })
  }
  const highestRemote = categories
    ?.filter((c) => c.category !== 'UNKNOWN_UNCLASSIFIED')
    .filter((c) => c.share >= MIN_SHARE_FOR_RATE)
    .sort((a, b) => b.remote_rate - a.remote_rate)[0]
  if (highestRemote) {
    insights.push({
      title: 'Highest Remote Handling',
      value: highestRemote.category,
      detail: `${formatPercent(highestRemote.remote_rate)} of its ${formatNumber(highestRemote.total)} issues were handled remotely.`,
    })
  }
  const peak = monthly?.reduce<TimePoint | null>((best, p) => (!best || p.total > best.total ? p : best), null)
  if (peak && peak.total > 0) {
    insights.push({
      title: 'Peak Support Period',
      value: peak.full_label,
      detail: `${formatNumber(peak.total)} issues logged, the highest monthly volume in the dataset.`,
    })
  }
  insights.push({
    title: 'Remote Handling Rate',
    value: formatPercent(data.remote_rate),
    detail: `${formatNumber(data.total_remote)} of ${formatNumber(data.total_remote + data.total_non_remote)} known outcomes were resolved remotely.`,
  })
  return insights
}

export function OverviewView() {
  const overview = useOverview()
  const issues = useIssues()
  const [period, setPeriod] = useState<Period>('monthly')
  const trend = useTimeSeries(period)
  const monthly = useTimeSeries('monthly')
  const data = overview.data

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Support Analytics Overview"
        description="Aggregated customer support issues, remote handling and volume trends."
      />

      {overview.error ? (
        <ErrorState onRetry={() => overview.mutate()} />
      ) : (
        <>
          <KpiRow items={data ? buildKpis(data) : null} loading={!data} count={5} compact />

          {data && data.total_issues === 0 ? (
            <div className="rounded-lg border bg-card">
              <EmptyState />
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
              <Panel
                title="Issue Distribution"
                description="Detected issues by category, ranked by volume"
                className="lg:col-span-3"
              >
                {data ? (
                  <CategoryBars items={data.categories.map((c) => ({ category: c.category, value: c.total, share: c.share }))} />
                ) : (
                  <BarListSkeleton />
                )}
              </Panel>
              <Panel title="Remote Handling Overview" description="How detected issues were resolved" className="lg:col-span-2">
                {data ? (
                  <HandlingDonut remote={data.total_remote} nonRemote={data.total_non_remote} unknown={data.total_unknown} remoteRate={data.remote_rate} />
                ) : (
                  <ChartSkeleton height={200} />
                )}
              </Panel>
            </div>
          )}
        </>
      )}

      <Panel
        title="Support Trend"
        description="Remote and non-remote issue volume over time"
        actions={
          <>
            <div className="mr-2 hidden items-center gap-4 md:flex">
              <LegendItem color={HANDLING_COLORS.remote} label="Remote" />
              <LegendItem color={HANDLING_COLORS.non_remote} label="Non-Remote" />
            </div>
            <PeriodSelector value={period} onChange={setPeriod} label="Support trend period" />
          </>
        }
      >
        {trend.error ? (
          <ErrorState message="The trend data could not be loaded." onRetry={() => trend.mutate()} className="border-0 p-0" />
        ) : trend.data ? (
          trend.data.points.length ? (
            <HandlingTrendChart points={trend.data.points} />
          ) : (
            <EmptyState message="No issues were recorded for this period." />
          )
        ) : (
          <ChartSkeleton />
        )}
      </Panel>

      {data && data.total_issues > 0 && (
        <Panel title="Category Performance" description="Issue volume and remote handling rate per category">
          {issues.error ? (
            <ErrorState message="Category performance could not be loaded." onRetry={() => issues.mutate()} className="border-0 p-0" />
          ) : issues.data ? (
            <CategoryPerformance categories={issues.data.categories} />
          ) : (
            <BarListSkeleton />
          )}
        </Panel>
      )}

      {data && data.total_issues > 0 && (
        <section aria-labelledby="key-insights">
          <h2 id="key-insights" className="text-sm font-semibold text-foreground">
            Key Insights
          </h2>
          <dl className="mt-3 grid grid-cols-1 border-t sm:grid-cols-2 xl:grid-cols-4">
            {buildInsights(data, issues.data?.categories, monthly.data?.points).map((insight) => (
              <div key={insight.title} className="flex flex-col gap-1 border-b py-4 sm:pr-6 xl:border-b-0">
                <dt className="text-xs font-medium text-muted-foreground">{insight.title}</dt>
                <dd className="break-all text-sm font-semibold tracking-tight text-foreground">{insight.value}</dd>
                <dd className="text-sm text-muted-foreground text-pretty">{insight.detail}</dd>
              </div>
            ))}
            {!monthly.data && <Skeleton className="m-4 h-12" aria-hidden="true" />}
          </dl>
        </section>
      )}
    </div>
  )
}
