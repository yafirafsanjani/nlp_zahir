import type { CategoryStat } from '@/lib/api/types'
import { CATEGORIES } from '@/lib/categories'
import { formatNumber, formatPercent } from '@/lib/format'
import { cn } from '@/lib/utils'

const HEADERS = [
  { label: 'Issue Category', align: 'left' },
  { label: 'Total', align: 'right' },
  { label: 'Remote', align: 'right' },
  { label: 'Non-Remote', align: 'right' },
  { label: 'Remote Rate', align: 'right' },
] as const

export function CategoryPerformance({ categories }: { categories: CategoryStat[] }) {
  const byCategory = new Map(categories.map((c) => [c.category, c]))
  const rows = CATEGORIES.map(
    (category) =>
      byCategory.get(category) ?? { category, total: 0, remote: 0, non_remote: 0, unknown: 0, remote_rate: 0, share: 0 },
  ).sort((a, b) => b.total - a.total)

  return (
    <div className="-mx-5 -mb-5 overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-sm">
        <caption className="sr-only">Issue volume and remote handling by category</caption>
        <thead>
          <tr className="border-b">
            {HEADERS.map((h) => (
              <th
                key={h.label}
                scope="col"
                className={cn(
                  'h-9 px-5 text-xs font-medium whitespace-nowrap text-muted-foreground',
                  h.align === 'right' ? 'text-right' : 'text-left',
                )}
              >
                {h.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.category} className="border-b transition-colors last:border-0 hover:bg-secondary/50">
              <th scope="row" className="h-10 px-5 text-left font-medium text-foreground">
                {row.category}
              </th>
              <td className="h-10 px-5 text-right tabular-nums text-foreground">{formatNumber(row.total)}</td>
              <td className="h-10 px-5 text-right tabular-nums text-muted-foreground">{formatNumber(row.remote)}</td>
              <td className="h-10 px-5 text-right tabular-nums text-muted-foreground">
                {formatNumber(row.non_remote)}
              </td>
              <td className="h-10 px-5 text-right">
                <div className="flex items-center justify-end gap-3">
                  <div className="hidden h-1.5 w-16 overflow-hidden rounded-full bg-secondary sm:block" aria-hidden="true">
                    <div className="h-full rounded-full bg-primary" style={{ width: `${row.remote_rate * 100}%` }} />
                  </div>
                  <span className="w-12 tabular-nums font-medium text-foreground">{formatPercent(row.remote_rate)}</span>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
