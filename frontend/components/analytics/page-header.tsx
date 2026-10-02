'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useSWRConfig } from 'swr'
import { Menu, RefreshCw, UploadCloud } from 'lucide-react'
import { Button, buttonVariants } from '@/components/ui/button'
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from '@/components/ui/sheet'
import { useDataset } from '@/components/providers/dataset-provider'
import { cn } from '@/lib/utils'
import { SidebarNav } from './sidebar-nav'

function DatasetIndicator() {
  const { dataset } = useDataset()
  const isSession = dataset.kind === 'session'
  return (
    <div className="hidden items-center gap-2 text-xs text-muted-foreground md:flex">
      <span aria-hidden="true" className={cn('size-1.5 rounded-full', isSession ? 'bg-primary' : 'bg-foreground')} />
      <span className="font-medium text-foreground">{isSession ? 'Session Dataset' : 'Default Dataset'}</span>
      {isSession && <span className="tabular-nums">· {dataset.sessionId}</span>}
    </div>
  )
}

function RefreshButton() {
  const { mutate } = useSWRConfig()
  const [refreshing, setRefreshing] = useState(false)
  async function refresh() {
    setRefreshing(true)
    await mutate(() => true)
    setRefreshing(false)
  }
  return (
    <Button variant="outline" size="sm" onClick={refresh} disabled={refreshing} aria-label="Refresh analytics">
      <RefreshCw aria-hidden="true" className={cn('size-3.5', refreshing && 'animate-spin')} />
      <span className="hidden sm:inline">Refresh</span>
    </Button>
  )
}

function MobileNav() {
  const [open, setOpen] = useState(false)
  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger
        render={
          <Button variant="outline" size="icon-sm" className="lg:hidden" aria-label="Open navigation">
            <Menu aria-hidden="true" className="size-4" />
          </Button>
        }
      />
      <SheetContent side="left" className="w-72 p-4 pt-6">
        <SheetTitle className="sr-only">Navigation</SheetTitle>
        <SidebarNav onNavigate={() => setOpen(false)} />
      </SheetContent>
    </Sheet>
  )
}

export function PageHeader({
  title,
  description,
  showActions = true,
}: {
  title: string
  description: string
  showActions?: boolean
}) {
  return (
    <header className="flex flex-col gap-4 border-b pb-6 sm:flex-row sm:items-end sm:justify-between">
      <div className="flex items-start gap-3">
        <MobileNav />
        <div className="min-w-0">
          <h1 className="text-2xl font-semibold tracking-tight text-foreground text-balance">{title}</h1>
          <p className="mt-1 text-sm text-muted-foreground text-pretty">{description}</p>
        </div>
      </div>
      {showActions && (
        <div className="flex shrink-0 items-center gap-3">
          <DatasetIndicator />
          <RefreshButton />
          <Link href="/data" className={buttonVariants({ size: 'sm' })}>
            <UploadCloud aria-hidden="true" className="size-3.5" />
            Add / Update Data
          </Link>
        </div>
      )}
    </header>
  )
}
