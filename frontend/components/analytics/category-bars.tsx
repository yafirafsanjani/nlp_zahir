import type { ApiCategory } from '@/lib/api/types'
import { formatNumber, formatPercent } from '@/lib/format'
import { cn } from '@/lib/utils'
import { CategoryName } from './panel'

export type CategoryBarItem = { category: ApiCategory; value: number; share: number }

export function CategoryBars({
  items,
  highlight,
  limit,
}: {
  items: CategoryBarItem[]
  highlight?: ApiCategory | null
  limit?: number
}) {
  const rows = limit ? items.slice(0, limit) : items
  const max = Math.max(...rows.map((r) => r.value), 1)
  return (
    <ol className="flex flex-col gap-3.5">
      {rows.map((row, index) => {
        const dimmed = highlight ? row.category !== highlight : false
        return (
          <li key={row.category} className={cn('flex flex-col gap-1.5 transition-opacity', dimmed && 'opacity-45')}>
            <div className="flex items-baseline justify-between gap-4">
              <div className="flex min-w-0 items-baseline gap-2.5">
                <span className="w-4 shrink-0 text-right text-xs tabular-nums text-muted-foreground">{index + 1}</span>
                <CategoryName value={row.category} />
              </div>
              <div className="flex shrink-0 items-baseline gap-3 tabular-nums">
                <span className="text-sm font-medium text-foreground">{formatNumber(row.value)}</span>
                <span className="w-12 text-right text-xs text-muted-foreground">{formatPercent(row.share)}</span>
              </div>
            </div>
            <div className="ml-6.5 h-1.5 overflow-hidden rounded-full bg-secondary">
              <div
                className={cn('h-full rounded-full', dimmed ? 'bg-muted-foreground/50' : 'bg-primary')}
                style={{ width: `${(row.value / max) * 100}%` }}
              />
            </div>
          </li>
        )
      })}
    </ol>
  )
}
