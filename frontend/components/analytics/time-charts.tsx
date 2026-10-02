'use client'

import { Area, AreaChart, Bar, BarChart, CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts'
import {
  ChartContainer,
  ChartTooltip,
  ChartTooltipContent,
  type ChartConfig,
} from '@/components/ui/chart'
import type { TimePoint } from '@/lib/api/types'
import { HANDLING_COLORS, HANDLING_LABELS } from '@/lib/chart-colors'
import { formatCompact } from '@/lib/format'

const tooltipLabel = (_: unknown, payload: ReadonlyArray<{ payload?: TimePoint }>) =>
  payload?.[0]?.payload?.full_label ?? ''

const axisProps = {
  tickLine: false,
  axisLine: false,
  tickMargin: 8,
  fontSize: 11,
} as const

function xInterval(count: number) {
  if (count <= 12) return 0
  return Math.ceil(count / 10) - 1
}

const volumeConfig = {
  total: { label: 'Total Issues', color: 'var(--chart-1)' },
} satisfies ChartConfig

export function VolumeAreaChart({ points, height = 280 }: { points: TimePoint[]; height?: number }) {
  return (
    <ChartContainer config={volumeConfig} className="w-full" style={{ height }}>
      <AreaChart data={points} margin={{ left: 4, right: 20, top: 8 }}>
        <defs>
          <linearGradient id="volume-fill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--color-total)" stopOpacity={0.18} />
            <stop offset="100%" stopColor="var(--color-total)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="label" interval={xInterval(points.length)} {...axisProps} />
        <YAxis width={40} tickFormatter={(v: number) => formatCompact(v)} allowDecimals={false} {...axisProps} />
        <ChartTooltip cursor={{ strokeDasharray: '3 3' }} content={<ChartTooltipContent labelFormatter={tooltipLabel} />} />
        <Area
          dataKey="total"
          type="monotone"
          stroke="var(--color-total)"
          strokeWidth={2}
          fill="url(#volume-fill)"
          isAnimationActive={false}
          activeDot={{ r: 4, strokeWidth: 0 }}
        />
      </AreaChart>
    </ChartContainer>
  )
}

const handlingConfig = {
  remote: { label: HANDLING_LABELS.remote, color: HANDLING_COLORS.remote },
  non_remote: { label: HANDLING_LABELS.non_remote, color: HANDLING_COLORS.non_remote },
  unknown: { label: HANDLING_LABELS.unknown, color: HANDLING_COLORS.unknown },
} satisfies ChartConfig

export function HandlingTrendChart({ points, height = 280 }: { points: TimePoint[]; height?: number }) {
  return (
    <ChartContainer config={handlingConfig} className="w-full" style={{ height }}>
      <LineChart data={points} margin={{ left: 4, right: 20, top: 8 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="label" interval={xInterval(points.length)} {...axisProps} />
        <YAxis width={40} tickFormatter={(v: number) => formatCompact(v)} allowDecimals={false} {...axisProps} />
        <ChartTooltip cursor={{ strokeDasharray: '3 3' }} content={<ChartTooltipContent labelFormatter={tooltipLabel} />} />
        <Line dataKey="remote" type="monotone" stroke="var(--color-remote)" strokeWidth={2} dot={false} isAnimationActive={false} />
        <Line
          dataKey="non_remote"
          type="monotone"
          stroke="var(--color-non_remote)"
          strokeWidth={2}
          dot={false}
          isAnimationActive={false}
        />
      </LineChart>
    </ChartContainer>
  )
}

export function HandlingStackedChart({ points, height = 280 }: { points: TimePoint[]; height?: number }) {
  return (
    <ChartContainer config={handlingConfig} className="w-full" style={{ height }}>
      <BarChart data={points} margin={{ left: 4, right: 20, top: 8 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="label" interval={xInterval(points.length)} {...axisProps} />
        <YAxis width={40} tickFormatter={(v: number) => formatCompact(v)} allowDecimals={false} {...axisProps} />
        <ChartTooltip cursor={{ fill: 'var(--muted)', opacity: 0.6 }} content={<ChartTooltipContent labelFormatter={tooltipLabel} />} />
        <Bar dataKey="remote" stackId="h" fill="var(--color-remote)" isAnimationActive={false} />
        <Bar dataKey="non_remote" stackId="h" fill="var(--color-non_remote)" isAnimationActive={false} />
        <Bar dataKey="unknown" stackId="h" fill="var(--color-unknown)" radius={[2, 2, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ChartContainer>
  )
}

/** The FastAPI time-series endpoint provides aggregate period volume. */
export function CategoryTrendChart({ points, height = 280 }: { points: TimePoint[]; height?: number }) {
  const data = points.map((p) => ({ ...p, value: p.total }))
  const config = {
    value: { label: 'All Categories', color: 'var(--chart-1)' },
  } satisfies ChartConfig
  return (
    <ChartContainer config={config} className="w-full" style={{ height }}>
      <LineChart data={data} margin={{ left: 4, right: 20, top: 8 }}>
        <CartesianGrid vertical={false} strokeDasharray="3 3" />
        <XAxis dataKey="label" interval={xInterval(data.length)} {...axisProps} />
        <YAxis width={40} tickFormatter={(v: number) => formatCompact(v)} allowDecimals={false} {...axisProps} />
        <ChartTooltip cursor={{ strokeDasharray: '3 3' }} content={<ChartTooltipContent labelFormatter={tooltipLabel} />} />
        <Line dataKey="value" type="monotone" stroke="var(--color-value)" strokeWidth={2} dot={false} isAnimationActive={false} />
      </LineChart>
    </ChartContainer>
  )
}
