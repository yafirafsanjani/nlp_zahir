'use client'

import { useState } from 'react'
import { PageHeader } from '@/components/analytics/page-header'
import { Panel, CategoryName } from '@/components/analytics/panel'
import { CategoryBars } from '@/components/analytics/category-bars'
import { HandlingLegend, HandlingSplit } from '@/components/analytics/handling-split'
import { CategoryTrendChart } from '@/components/analytics/time-charts'
import { CategorySelect, PeriodSelector } from '@/components/analytics/filters'
import { DataTable, type Column } from '@/components/analytics/data-table'
import { BarListSkeleton, ChartSkeleton, EmptyState, ErrorState, TableSkeleton } from '@/components/analytics/states'
import { useIssues, useTimeSeries } from '@/lib/api/hooks'
import type { CategoryStat } from '@/lib/api/types'
import { ALL_CATEGORIES, type CategoryFilter, type Period } from '@/lib/categories'
import { formatNumber, formatPercent } from '@/lib/format'

const columns: Column<CategoryStat>[] = [
  {
    key: 'category',
    header: 'Category',
    sortValue: (r) => r.category,
    cell: (r) => <CategoryName value={r.category} />,
  },
  { key: 'total', header: 'Total Issues', align: 'right', sortValue: (r) => r.total, cell: (r) => formatNumber(r.total) },
  {
    key: 'share',
    header: 'Share',
    align: 'right',
    sortValue: (r) => r.share,
    cell: (r) => <span className="text-muted-foreground">{formatPercent(r.share)}</span>,
  },
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
    sortValue: (r) => r.remote_rate,
    cell: (r) => <span className="font-medium">{formatPercent(r.remote_rate)}</span>,
  },
]

export function IssuesView() {
  const issues = useIssues()
  const [category, setCategory] = useState<CategoryFilter>(ALL_CATEGORIES)
  const [period, setPeriod] = useState<Period>('monthly')
  const trend = useTimeSeries(period)
  const selected = category === ALL_CATEGORIES ? null : category
  const data = issues.data
  const tableRows = data ? (selected ? data.categories.filter((c) => c.category === selected) : data.categories) : []

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Issue Analysis"
        description="Volume and handling method for each official issue category."
      />

      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
        <label htmlFor="issue-category" className="text-xs font-medium text-muted-foreground">
          Category
        </label>
        <CategorySelect id="issue-category" value={category} onChange={setCategory} />
      </div>

      {issues.error ? (
        <ErrorState onRetry={() => issues.mutate()} />
      ) : data && data.total_issues === 0 ? (
        <div className="rounded-lg border bg-card">
          <EmptyState />
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <Panel title="Issue Category Distribution" description="Share of all detected issues">
              {data ? (
                <CategoryBars
                  highlight={selected}
                  items={data.categories.map((c) => ({ category: c.category, value: c.total, share: c.share }))}
                />
              ) : (
                <BarListSkeleton />
              )}
            </Panel>
            <Panel title="Remote vs Non-Remote by Category" actions={<HandlingLegend />}>
              {data ? <HandlingSplit items={data.categories} highlight={selected} /> : <BarListSkeleton />}
            </Panel>
          </div>

          <Panel
            title="Support Volume Trend"
            description="Time-series volume across all categories for the selected period."
            actions={<PeriodSelector value={period} onChange={setPeriod} label="Category trend period" />}
          >
            {trend.error ? (
              <ErrorState message="The trend data could not be loaded." onRetry={() => trend.mutate()} className="border-0 p-0" />
            ) : trend.data ? (
              <CategoryTrendChart points={trend.data.points} />
            ) : (
              <ChartSkeleton />
            )}
          </Panel>

          <Panel title="Issue Category Summary" description="Aggregated counts per category" bodyClassName="pt-2">
            {data ? (
              <DataTable
                caption="Issue category summary"
                columns={columns}
                rows={tableRows}
                rowKey={(r) => r.category}
                initialSort={{ key: 'total', direction: 'desc' }}
              />
            ) : (
              <TableSkeleton columns={6} rows={9} />
            )}
          </Panel>
        </>
      )}
    </div>
  )
}
