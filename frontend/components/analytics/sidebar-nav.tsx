'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { useDataset } from '@/components/providers/dataset-provider'
import { ANALYSIS_NAV, DATA_NAV, type NavItem } from './nav-items'

export function Brand() {
  return (
    <Link href="/" className="flex items-center gap-3 rounded-md outline-none focus-visible:ring-3 focus-visible:ring-ring">
      <span
        aria-hidden="true"
        className="flex size-8 items-center justify-center rounded-md bg-primary text-[13px] font-bold text-primary-foreground"
      >
        Z
      </span>
      <span className="flex flex-col leading-tight">
        <span className="text-sm font-semibold text-foreground">NLP Support Center</span>
        <span className="text-xs text-muted-foreground">Zahir Analytics</span>
      </span>
    </Link>
  )
}

function NavLink({ item, onNavigate }: { item: NavItem; onNavigate?: () => void }) {
  const pathname = usePathname()
  const active = item.href === '/' ? pathname === '/' : pathname.startsWith(item.href)
  const Icon = item.icon
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      aria-current={active ? 'page' : undefined}
      className={cn(
        'group relative flex h-9 items-center gap-3 rounded-md px-3 text-sm outline-none transition-colors focus-visible:ring-3 focus-visible:ring-ring',
        active
          ? 'bg-secondary font-medium text-foreground'
          : 'text-muted-foreground hover:bg-secondary/70 hover:text-foreground',
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          'absolute inset-y-2 left-0 w-0.5 rounded-full transition-colors',
          active ? 'bg-primary' : 'bg-transparent',
        )}
      />
      <Icon
        aria-hidden="true"
        strokeWidth={1.75}
        className={cn('size-4 shrink-0', active ? 'text-primary' : 'text-muted-foreground group-hover:text-foreground')}
      />
      {item.label}
    </Link>
  )
}

function DatasetStatusPanel() {
  const { dataset, resetToDefault } = useDataset()
  const isSession = dataset.kind === 'session'
  return (
    <div className="rounded-lg border bg-background p-3">
      <p className="text-[11px] font-medium uppercase tracking-wider text-muted-foreground">Dataset Status</p>
      <div className="mt-2 flex items-center gap-2">
        <span
          aria-hidden="true"
          className={cn('size-1.5 rounded-full', isSession ? 'bg-primary' : 'bg-foreground')}
        />
        <span className="text-sm font-medium text-foreground">
          {isSession ? 'Session Dataset' : 'Default Dataset'}
        </span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground">
        {isSession ? `Session ID: ${dataset.sessionId}` : 'Ready · analytics available'}
      </p>
      {isSession && (
        <button
          type="button"
          onClick={resetToDefault}
          className="mt-2 text-xs font-medium text-foreground underline-offset-4 outline-none hover:underline focus-visible:underline"
        >
          Switch to default dataset
        </button>
      )}
    </div>
  )
}

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <div className="flex h-full flex-col gap-8">
      <Brand />
      <nav aria-label="Main" className="flex flex-1 flex-col gap-6">
        <div className="flex flex-col gap-0.5">
          <p className="mb-1.5 px-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Analytics
          </p>
          {ANALYSIS_NAV.map((item) => (
            <NavLink key={item.href} item={item} onNavigate={onNavigate} />
          ))}
        </div>
        <div className="flex flex-col gap-0.5 border-t pt-6">
          <p className="mb-1.5 px-3 text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
            Data Management
          </p>
          {DATA_NAV.map((item) => (
            <NavLink key={item.href} item={item} onNavigate={onNavigate} />
          ))}
        </div>
      </nav>
      <DatasetStatusPanel />
    </div>
  )
}

export function AppSidebar() {
  return (
    <aside className="sticky top-0 hidden h-dvh w-64 shrink-0 border-r bg-sidebar px-4 py-6 lg:block">
      <SidebarNav />
    </aside>
  )
}
