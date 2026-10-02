import { AlertCircle, Inbox, RotateCw } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

export function ErrorState({
  title = 'Unable to load analytics',
  message = 'Something went wrong while loading the data.',
  onRetry,
  className,
}: {
  title?: string
  message?: string
  onRetry?: () => void
  className?: string
}) {
  return (
    <div role="alert" className={cn('flex flex-col items-start gap-3 rounded-lg border bg-card p-5', className)}>
      <div className="flex items-start gap-3">
        <AlertCircle aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" strokeWidth={2} />
        <div>
          <p className="text-sm font-medium text-foreground">{title}</p>
          <p className="mt-0.5 text-sm text-muted-foreground">{message}</p>
        </div>
      </div>
      {onRetry && (
        <Button variant="outline" size="sm" onClick={onRetry} className="ml-7">
          <RotateCw aria-hidden="true" className="size-3.5" />
          Retry
        </Button>
      )}
    </div>
  )
}

export function EmptyState({
  title = 'No analytics data available',
  message = 'There is no aggregated data for the current selection.',
  className,
}: {
  title?: string
  message?: string
  className?: string
}) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-2 py-12 text-center', className)}>
      <Inbox aria-hidden="true" className="size-5 text-muted-foreground" strokeWidth={1.5} />
      <p className="text-sm font-medium text-foreground">{title}</p>
      <p className="max-w-sm text-sm text-muted-foreground text-pretty">{message}</p>
    </div>
  )
}

export function ChartSkeleton({ height = 280 }: { height?: number }) {
  return (
    <div aria-hidden="true" className="flex items-end gap-2" style={{ height }}>
      {[42, 58, 50, 66, 54, 72, 64, 80, 70, 86, 76, 68].map((h, i) => (
        <Skeleton key={i} className="flex-1 rounded-sm" style={{ height: `${h}%` }} />
      ))}
    </div>
  )
}

export function BarListSkeleton({ rows = 9 }: { rows?: number }) {
  return (
    <div aria-hidden="true" className="flex flex-col gap-4">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex flex-col gap-2">
          <div className="flex justify-between">
            <Skeleton className="h-3 w-40" />
            <Skeleton className="h-3 w-12" />
          </div>
          <Skeleton className="h-1.5 rounded-full" style={{ width: `${90 - i * 8}%` }} />
        </div>
      ))}
    </div>
  )
}

export function TableSkeleton({ rows = 8, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div aria-hidden="true" className="flex flex-col">
      <div className="flex gap-6 border-b pb-3">
        {Array.from({ length: columns }, (_, i) => (
          <Skeleton key={i} className={cn('h-3', i === 0 ? 'w-48' : 'ml-auto w-14')} />
        ))}
      </div>
      {Array.from({ length: rows }, (_, r) => (
        <div key={r} className="flex gap-6 border-b py-3.5 last:border-0">
          {Array.from({ length: columns }, (_, i) => (
            <Skeleton key={i} className={cn('h-3', i === 0 ? 'w-56' : 'ml-auto w-12')} />
          ))}
        </div>
      ))}
    </div>
  )
}
