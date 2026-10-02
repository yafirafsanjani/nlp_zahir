const integer = new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 })
const oneDecimal = new Intl.NumberFormat('en-US', {
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
})
const compact = new Intl.NumberFormat('en-US', {
  notation: 'compact',
  maximumFractionDigits: 1,
})
const dateFormat = new Intl.DateTimeFormat('en-GB', {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
  timeZone: 'UTC',
})

export const formatNumber = (value: number) => integer.format(value)
export const formatDecimal = (value: number) => oneDecimal.format(value)
export const formatCompact = (value: number) => compact.format(value)
export const formatPercent = (ratio: number) => `${oneDecimal.format(ratio * 100)}%`
export const formatDate = (iso: string) => dateFormat.format(new Date(iso))
export const formatDateRange = (range: { start: string; end: string } | null) =>
  range ? `${formatDate(range.start)} – ${formatDate(range.end)}` : '—'
