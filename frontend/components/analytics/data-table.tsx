'use client'

import { useMemo, useState } from 'react'
import { ArrowDown, ArrowUp, ChevronLeft, ChevronRight, ChevronsUpDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'
import { EmptyState } from './states'

export type Column<T> = {
  key: string
  header: string
  align?: 'left' | 'right'
  sortValue?: (row: T) => number | string
  cell: (row: T) => React.ReactNode
  className?: string
}

export function DataTable<T>({
  caption,
  columns,
  rows,
  rowKey,
  initialSort,
  pageSize = 10,
  emptyTitle,
  emptyMessage,
}: {
  caption: string
  columns: Column<T>[]
  rows: T[]
  rowKey: (row: T) => string
  initialSort?: { key: string; direction: 'asc' | 'desc' }
  pageSize?: number
  emptyTitle?: string
  emptyMessage?: string
}) {
  const [sort, setSort] = useState(initialSort ?? null)
  const [page, setPage] = useState(0)

  const sorted = useMemo(() => {
    if (!sort) return rows
    const column = columns.find((c) => c.key === sort.key)
    if (!column?.sortValue) return rows
    const getValue = column.sortValue
    return [...rows].sort((a, b) => {
      const av = getValue(a)
      const bv = getValue(b)
      const result = typeof av === 'number' && typeof bv === 'number' ? av - bv : String(av).localeCompare(String(bv))
      return sort.direction === 'asc' ? result : -result
    })
  }, [rows, columns, sort])

  const pageCount = Math.max(1, Math.ceil(sorted.length / pageSize))
  const currentPage = Math.min(page, pageCount - 1)
  const visible = sorted.slice(currentPage * pageSize, (currentPage + 1) * pageSize)

  function toggleSort(key: string) {
    setPage(0)
    setSort((prev) =>
      prev?.key === key ? { key, direction: prev.direction === 'desc' ? 'asc' : 'desc' } : { key, direction: 'desc' },
    )
  }

  if (!rows.length) return <EmptyState title={emptyTitle} message={emptyMessage} />

  return (
    <div className="flex flex-col">
      <div className="-mx-5 overflow-x-auto">
        <table className="w-full min-w-[640px] border-collapse text-sm">
          <caption className="sr-only">{caption}</caption>
          <thead>
            <tr className="border-b">
              {columns.map((column) => {
                const active = sort?.key === column.key
                const ariaSort = active ? (sort.direction === 'asc' ? 'ascending' : 'descending') : 'none'
                const Icon = active ? (sort.direction === 'asc' ? ArrowUp : ArrowDown) : ChevronsUpDown
                return (
                  <th
                    key={column.key}
                    scope="col"
                    aria-sort={column.sortValue ? ariaSort : undefined}
                    className={cn(
                      'h-10 px-5 text-xs font-medium whitespace-nowrap text-muted-foreground',
                      column.align === 'right' ? 'text-right' : 'text-left',
                      column.className,
                    )}
                  >
                    {column.sortValue ? (
                      <button
                        type="button"
                        onClick={() => toggleSort(column.key)}
                        className={cn(
                          'inline-flex items-center gap-1 rounded-sm outline-none hover:text-foreground focus-visible:ring-2 focus-visible:ring-ring',
                          column.align === 'right' && 'flex-row-reverse',
                          active && 'text-foreground',
                        )}
                      >
                        {column.header}
                        <Icon aria-hidden="true" className={cn('size-3', !active && 'opacity-50')} />
                      </button>
                    ) : (
                      column.header
                    )}
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {visible.map((row) => (
              <tr key={rowKey(row)} className="border-b transition-colors last:border-0 hover:bg-secondary/50">
                {columns.map((column) => (
                  <td
                    key={column.key}
                    className={cn(
                      'h-12 px-5 tabular-nums',
                      column.align === 'right' ? 'text-right' : 'text-left',
                      column.className,
                    )}
                  >
                    {column.cell(row)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {pageCount > 1 && (
        <div className="-mx-5 -mb-5 mt-0 flex items-center justify-between border-t px-5 py-3">
          <p className="text-xs text-muted-foreground tabular-nums">
            {currentPage * pageSize + 1}–{Math.min((currentPage + 1) * pageSize, sorted.length)} of {sorted.length}
          </p>
          <div className="flex items-center gap-1">
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => setPage(currentPage - 1)}
              disabled={currentPage === 0}
              aria-label="Previous page"
            >
              <ChevronLeft aria-hidden="true" />
            </Button>
            <span className="px-2 text-xs text-muted-foreground tabular-nums">
              {currentPage + 1} / {pageCount}
            </span>
            <Button
              variant="outline"
              size="icon-sm"
              onClick={() => setPage(currentPage + 1)}
              disabled={currentPage >= pageCount - 1}
              aria-label="Next page"
            >
              <ChevronRight aria-hidden="true" />
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
