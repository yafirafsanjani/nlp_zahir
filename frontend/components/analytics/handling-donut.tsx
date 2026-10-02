'use client'

import { Cell, Label, Pie, PieChart } from 'recharts'
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from '@/components/ui/chart'
import { HANDLING_COLORS, HANDLING_LABELS } from '@/lib/chart-colors'
import { formatNumber, formatPercent } from '@/lib/format'

const config = {
  remote: { label: HANDLING_LABELS.remote, color: HANDLING_COLORS.remote },
  non_remote: { label: HANDLING_LABELS.non_remote, color: HANDLING_COLORS.non_remote },
  unknown: { label: HANDLING_LABELS.unknown, color: HANDLING_COLORS.unknown },
} satisfies ChartConfig

export function HandlingDonut({
  remote,
  nonRemote,
  unknown,
  remoteRate,
}: {
  remote: number
  nonRemote: number
  unknown: number
  remoteRate: number
}) {
  const total = remote + nonRemote + unknown
  const data = [
    { key: 'remote', value: remote },
    { key: 'non_remote', value: nonRemote },
    { key: 'unknown', value: unknown },
  ] as const

  return (
    <div className="flex flex-wrap items-center justify-center gap-6">
      <ChartContainer config={config} className="aspect-square h-[200px] shrink-0">
        <PieChart>
          <ChartTooltip cursor={false} content={<ChartTooltipContent nameKey="key" hideLabel />} />
          <Pie
            data={[...data]}
            dataKey="value"
            nameKey="key"
            innerRadius={66}
            outerRadius={92}
            paddingAngle={1.5}
            strokeWidth={0}
            isAnimationActive={false}
          >
            {data.map((d) => (
              <Cell key={d.key} fill={`var(--color-${d.key})`} />
            ))}
            <Label
              content={({ viewBox }) => {
                if (!viewBox || !('cx' in viewBox)) return null
                return (
                  <text x={viewBox.cx} y={viewBox.cy} textAnchor="middle" dominantBaseline="middle">
                    <tspan x={viewBox.cx} y={(viewBox.cy ?? 0) - 8} className="fill-foreground text-2xl font-semibold">
                      {formatPercent(remoteRate)}
                    </tspan>
                    <tspan x={viewBox.cx} y={(viewBox.cy ?? 0) + 14} className="fill-muted-foreground text-xs">
                      handled remotely
                    </tspan>
                  </text>
                )
              }}
            />
          </Pie>
        </PieChart>
      </ChartContainer>
      <dl className="flex min-w-[220px] flex-1 flex-col divide-y">
        {data.map((d) => (
          <div key={d.key} className="flex items-center justify-between gap-4 py-2.5 first:pt-0 last:pb-0">
            <dt className="flex items-center gap-2 text-sm text-muted-foreground">
              <span aria-hidden="true" className="size-2 rounded-[2px]" style={{ backgroundColor: HANDLING_COLORS[d.key] }} />
              {HANDLING_LABELS[d.key]}
            </dt>
            <dd className="flex items-baseline gap-3 tabular-nums">
              <span className="text-sm font-medium text-foreground">{formatNumber(d.value)}</span>
              <span className="w-12 text-right text-xs text-muted-foreground">
                {formatPercent(total ? d.value / total : 0)}
              </span>
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
