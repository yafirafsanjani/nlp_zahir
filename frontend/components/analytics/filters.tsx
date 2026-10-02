'use client'

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import {
  ALL_CATEGORIES,
  CATEGORIES,
  PERIOD_LABELS,
  PERIODS,
  type CategoryFilter,
  type Period,
} from '@/lib/categories'
import { cn } from '@/lib/utils'

export function PeriodSelector({
  value,
  onChange,
  label = 'Period',
}: {
  value: Period
  onChange: (period: Period) => void
  label?: string
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex h-8 items-center rounded-md border bg-secondary/60 p-0.5">
      {PERIODS.map((period) => {
        const active = period === value
        return (
          <button
            key={period}
            type="button"
            role="radio"
            aria-checked={active}
            onClick={() => onChange(period)}
            className={cn(
              'h-full rounded-[5px] px-2.5 text-xs font-medium outline-none transition-colors focus-visible:ring-2 focus-visible:ring-ring',
              active
                ? 'bg-background text-foreground shadow-xs ring-1 ring-border'
                : 'text-muted-foreground hover:text-foreground',
            )}
          >
            {PERIOD_LABELS[period]}
          </button>
        )
      })}
    </div>
  )
}

const categoryItems = [
  { value: ALL_CATEGORIES, label: 'All Categories' },
  ...CATEGORIES.map((c) => ({ value: c, label: c })),
]

export function CategorySelect({
  value,
  onChange,
  id,
}: {
  value: CategoryFilter
  onChange: (value: CategoryFilter) => void
  id?: string
}) {
  return (
    <Select items={categoryItems} value={value} onValueChange={(v) => v && onChange(v as CategoryFilter)}>
      <SelectTrigger id={id} className="w-full min-w-0 bg-background sm:w-72" aria-label="Issue category">
        <SelectValue />
      </SelectTrigger>
      <SelectContent align="start" alignItemWithTrigger={false} className="min-w-72">
        {categoryItems.map((item) => (
          <SelectItem key={item.value} value={item.value} className="text-[13px]">
            {item.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
