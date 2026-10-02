import type { LucideIcon } from 'lucide-react'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export type Kpi = {
  label: string
  value: string
  context: string
  icon: LucideIcon
  emphasis?: boolean
  /** Long text values (e.g. category labels) render smaller to stay on one line. */
  textValue?: boolean
}

const GRID: Record<number, string> = {
  4: 'sm:grid-cols-2 xl:grid-cols-4',
  5: 'sm:grid-cols-2 xl:grid-cols-5',
}

export function KpiRow({
  items,
  loading,
  count: countHint,
  compact,
}: {
  items: Kpi[] | null
  loading?: boolean
  count?: number
  /** Tighter padding and a 3 → 5 column grid for dense rows. */
  compact?: boolean
}) {
  const count = items?.length ?? countHint ?? 4
  const padding = compact ? 'p-4' : 'p-5'
  return (
    <section
      aria-label="Key metrics"
      className={cn(
        'grid grid-cols-1 gap-px overflow-hidden rounded-lg border bg-border',
        compact ? 'grid-cols-2 sm:grid-cols-3 lg:grid-cols-5' : (GRID[count] ?? GRID[4]),
        compact && '[&>*:last-child]:col-span-2 sm:[&>*:last-child]:col-span-1',
        '[&>*]:bg-card',
      )}
    >
      {loading || !items
        ? Array.from({ length: count }, (_, i) => (
            <div key={i} className={cn('flex flex-col gap-3', padding)} aria-hidden="true">
              <Skeleton className="h-3 w-24" />
              <Skeleton className="h-7 w-28" />
              <Skeleton className="h-3 w-32" />
            </div>
          ))
        : items.map((item) => (
            <div key={item.label} className={cn('flex min-w-0 flex-col gap-1.5', padding)}>
              <div className="flex items-center justify-between gap-2">
                <p className="text-xs font-medium text-muted-foreground">{item.label}</p>
                <item.icon aria-hidden="true" strokeWidth={1.75} className="size-4 text-muted-foreground" />
              </div>
              <p
                className={cn(
                  'font-semibold tracking-tight tabular-nums',
                  item.textValue
                    ? 'truncate pt-1.5 pb-0.5 text-sm'
                    : compact
                      ? 'text-2xl leading-8'
                      : 'text-[28px] leading-9',
                  item.emphasis ? 'text-primary' : 'text-foreground',
                )}
                title={item.textValue ? item.value : undefined}
              >
                {item.value}
              </p>
              <p className="text-xs text-muted-foreground">{item.context}</p>
            </div>
          ))}
    </section>
  )
}
