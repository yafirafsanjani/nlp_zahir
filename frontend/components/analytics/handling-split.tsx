import type { Category } from '@/lib/categories'
import type { CategoryStat } from '@/lib/api/types'
import { HANDLING_COLORS, HANDLING_LABELS } from '@/lib/chart-colors'
import { formatNumber, formatPercent } from '@/lib/format'
import { cn } from '@/lib/utils'
import { CategoryName, LegendItem } from './panel'

export function HandlingLegend() {
  return (
    <div className="flex flex-wrap items-center gap-4">
      <LegendItem color={HANDLING_COLORS.remote} label={HANDLING_LABELS.remote} />
      <LegendItem color={HANDLING_COLORS.non_remote} label={HANDLING_LABELS.non_remote} />
      <LegendItem color={HANDLING_COLORS.unknown} label={HANDLING_LABELS.unknown} />
    </div>
  )
}

/** 100% stacked bars of remote vs non-remote handling per category. */
export function HandlingSplit({
  items,
  highlight,
  sortBy = 'total',
}: {
  items: CategoryStat[]
  highlight?: Category | null
  sortBy?: 'total' | 'remote_rate'
}) {
  const rows = [...items].sort((a, b) => b[sortBy] - a[sortBy])
  return (
    <ul className="flex flex-col gap-3.5">
      {rows.map((row) => {
        const dimmed = highlight ? row.category !== highlight : false
        const segments = (['remote', 'non_remote', 'unknown'] as const).map((key) => ({
          key,
          value: row[key],
          ratio: row.total ? row[key] / row.total : 0,
        }))
        return (
          <li key={row.category} className={cn('flex flex-col gap-1.5 transition-opacity', dimmed && 'opacity-40')}>
            <div className="flex items-baseline justify-between gap-4">
              <CategoryName value={row.category} />
              <span className="shrink-0 text-xs tabular-nums text-muted-foreground">
                <span className="font-medium text-foreground">{formatPercent(row.remote_rate)}</span> remote ·{' '}
                {formatNumber(row.total)}
              </span>
            </div>
            <div
              role="img"
              aria-label={`${row.category}: ${formatNumber(row.remote)} remote, ${formatNumber(row.non_remote)} non-remote, ${formatNumber(row.unknown)} unknown`}
              className="flex h-2 gap-px overflow-hidden rounded-full bg-secondary"
            >
              {segments.map((s) =>
                s.value > 0 ? (
                  <div
                    key={s.key}
                    className="h-full first:rounded-l-full last:rounded-r-full"
                    style={{ width: `${s.ratio * 100}%`, backgroundColor: HANDLING_COLORS[s.key] }}
                  />
                ) : null,
              )}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
