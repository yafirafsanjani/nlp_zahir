'use client'

import { useDeferredValue, useState } from 'react'
import { Activity, Search, UserRound, Users } from 'lucide-react'
import { PageHeader } from '@/components/analytics/page-header'
import { KpiRow, type Kpi } from '@/components/analytics/kpi-row'
import { Panel, CategoryName } from '@/components/analytics/panel'
import { DataTable, type Column } from '@/components/analytics/data-table'
import { BarListSkeleton, EmptyState, ErrorState, TableSkeleton } from '@/components/analytics/states'
import { Input } from '@/components/ui/input'
import { useCustomers } from '@/lib/api/hooks'
import type { CustomersData, CustomerStat } from '@/lib/api/types'
import { formatDecimal, formatNumber, formatPercent } from '@/lib/format'

function buildKpis(data: CustomersData): Kpi[] {
  const top = data.customers[0]
  return [
    {
      label: 'Total Customers',
      value: formatNumber(data.total_customers),
      context: 'With at least one detected issue',
      icon: Users,
    },
    {
      label: 'Avg Issues per Customer',
      value: formatDecimal(data.avg_issues_per_customer),
      context: `Across ${formatNumber(data.total_issues)} issues`,
      icon: Activity,
    },
    {
      label: 'Highest Issue Customer',
      value: top?.customer ?? '—',
      context: top ? `${formatNumber(top.total)} issues · ${formatPercent(top.total / data.total_issues)} of total` : '—',
      icon: UserRound,
      textValue: true,
    },
  ]
}

const columns: Column<CustomerStat>[] = [
  {
    key: 'customer',
    header: 'Customer',
    sortValue: (r) => r.customer,
    cell: (r) => <span className="font-medium whitespace-nowrap text-foreground">{r.customer}</span>,
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
    sortValue: (r) => r.remote_rate,
    cell: (r) => formatPercent(r.remote_rate),
  },
  {
    key: 'top_issue',
    header: 'Top Issue',
    sortValue: (r) => r.top_issue ?? '',
    cell: (r) => (r.top_issue ? <CategoryName value={r.top_issue} className="font-normal" /> : '—'),
  },
]

function TopCustomers({ customers }: { customers: CustomerStat[] }) {
  const top = customers.slice(0, 10)
  const max = Math.max(...top.map((c) => c.total), 1)
  return (
    <ol className="flex flex-col gap-3">
      {top.map((c, i) => (
        <li key={c.customer} className="grid grid-cols-[1rem_minmax(0,9.5rem)_1fr_3rem] items-center gap-3">
          <span className="text-right text-xs tabular-nums text-muted-foreground">{i + 1}</span>
          <span className="truncate text-[13px] font-medium tabular-nums text-foreground">{c.customer}</span>
          <div className="h-1.5 overflow-hidden rounded-full bg-secondary">
            <div
              className={i === 0 ? 'h-full rounded-full bg-primary' : 'h-full rounded-full bg-foreground/80'}
              style={{ width: `${(c.total / max) * 100}%` }}
            />
          </div>
          <span className="text-right text-sm font-medium tabular-nums text-foreground">{formatNumber(c.total)}</span>
        </li>
      ))}
    </ol>
  )
}

function Concentration({ data }: { data: CustomersData }) {
  const sumTop = (n: number) => data.customers.slice(0, n).reduce((s, c) => s + c.total, 0)
  const singleIssue = data.customers.filter((c) => c.total === 1).length
  const rows = [
    { label: 'Top 10 customers', value: formatPercent(sumTop(10) / data.total_issues), detail: 'of all issues' },
    { label: 'Top 25 customers', value: formatPercent(sumTop(25) / data.total_issues), detail: 'of all issues' },
    {
      label: 'Single-issue customers',
      value: formatNumber(singleIssue),
      detail: `${formatPercent(singleIssue / data.total_customers)} of customers`,
    },
  ]
  return (
    <dl className="flex flex-col divide-y">
      {rows.map((r) => (
        <div key={r.label} className="flex items-baseline justify-between gap-4 py-3.5 first:pt-0 last:pb-0">
          <dt className="text-sm text-muted-foreground">{r.label}</dt>
          <dd className="text-right">
            <span className="block text-xl font-semibold tracking-tight tabular-nums text-foreground">{r.value}</span>
            <span className="text-xs text-muted-foreground">{r.detail}</span>
          </dd>
        </div>
      ))}
    </dl>
  )
}

export function CustomersView() {
  const customers = useCustomers()
  const [query, setQuery] = useState('')
  const deferredQuery = useDeferredValue(query)
  const data = customers.data
  const normalized = deferredQuery.trim().toLowerCase()
  const filtered = data
    ? normalized
      ? data.customers.filter((c) => c.customer.toLowerCase().includes(normalized))
      : data.customers
    : []

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Customer Analysis"
        description="Issue volume and handling patterns aggregated per customer."
      />

      {customers.error ? (
        <ErrorState onRetry={() => customers.mutate()} />
      ) : data && data.total_customers === 0 ? (
        <div className="rounded-lg border bg-card">
          <EmptyState />
        </div>
      ) : (
        <>
          <KpiRow items={data ? buildKpis(data) : null} loading={!data} />

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
            <Panel title="Top 10 Customer Activity" description="Customers ranked by detected issues" className="lg:col-span-3">
              {data ? <TopCustomers customers={data.customers} /> : <BarListSkeleton rows={10} />}
            </Panel>
            <Panel title="Issue Concentration" description="How support volume is spread across customers" className="lg:col-span-2">
              {data ? <Concentration data={data} /> : <BarListSkeleton rows={3} />}
            </Panel>
          </div>

          <Panel
            title="Customer Summary"
            description={data ? `${formatNumber(filtered.length)} customers` : 'Loading customers'}
            bodyClassName="pt-2"
            actions={
              <div className="relative w-full sm:w-64">
                <Search
                  aria-hidden="true"
                  className="pointer-events-none absolute top-1/2 left-2.5 size-3.5 -translate-y-1/2 text-muted-foreground"
                />
                <Input
                  type="search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search customer"
                  aria-label="Search customer"
                  className="pl-8"
                />
              </div>
            }
          >
            {data ? (
              <DataTable
                key={normalized}
                caption="Customer summary"
                columns={columns}
                rows={filtered}
                rowKey={(r) => r.customer}
                initialSort={{ key: 'total', direction: 'desc' }}
                emptyTitle="No matching customers"
                emptyMessage="Try a different search term."
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
