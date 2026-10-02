import { cn } from '@/lib/utils'

export function Panel({
  title,
  description,
  actions,
  children,
  className,
  bodyClassName,
}: {
  title: string
  description?: string
  actions?: React.ReactNode
  children: React.ReactNode
  className?: string
  bodyClassName?: string
}) {
  const headingId = `panel-${title.toLowerCase().replace(/[^a-z0-9]+/g, '-')}`
  return (
    <section aria-labelledby={headingId} className={cn('flex min-w-0 flex-col rounded-lg border bg-card', className)}>
      <div className="flex flex-col gap-3 px-5 pt-5 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 id={headingId} className="text-sm font-semibold text-foreground">
            {title}
          </h2>
          {description && <p className="mt-0.5 text-xs text-muted-foreground">{description}</p>}
        </div>
        {actions && <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>}
      </div>
      <div className={cn('flex-1 px-5 pt-4 pb-5', bodyClassName)}>{children}</div>
    </section>
  )
}

export function LegendItem({ color, label }: { color: string; label: string }) {
  return (
    <span className="flex items-center gap-1.5 text-xs text-muted-foreground">
      <span aria-hidden="true" className="size-2 rounded-[2px]" style={{ backgroundColor: color }} />
      {label}
    </span>
  )
}

export function CategoryName({ value, className }: { value: string; className?: string }) {
  return (
    <span className={cn('break-all text-[12.5px] font-medium tracking-tight text-foreground', className)}>
      {value}
    </span>
  )
}
