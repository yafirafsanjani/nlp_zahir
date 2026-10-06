'use client'

import { useDeferredValue, useState } from 'react'
import {
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Download,
  FileSpreadsheet,
  FileText,
  Filter,
  Headset,
  HelpCircle,
  MessageSquare,
  RefreshCw,
  Search,
  ShieldAlert,
  SlidersHorizontal,
  XCircle,
} from 'lucide-react'
import { PageHeader } from '@/components/analytics/page-header'
import { Panel } from '@/components/analytics/panel'
import { KpiRow, type Kpi } from '@/components/analytics/kpi-row'
import { Button, buttonVariants } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { useConversations } from '@/lib/api/hooks'
import { getDownloadUrl } from '@/lib/api/client'
import { useDataset } from '@/components/providers/dataset-provider'
import type { ConversationRecord } from '@/lib/api/types'
import { CATEGORIES } from '@/lib/categories'
import { formatNumber, formatPercent } from '@/lib/format'
import { cn } from '@/lib/utils'

export function ConversationsView() {
  const { sessionId } = useDataset()
  const [searchInput, setSearchInput] = useState('')
  const [category, setCategory] = useState('')
  const [remote, setRemote] = useState('')
  const [clientResponse, setClientResponse] = useState('')
  const [match, setMatch] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // Selected conversation for Chat Transcript Drawer
  const [selectedRecord, setSelectedRecord] = useState<ConversationRecord | null>(null)

  const deferredSearch = useDeferredValue(searchInput)

  const { data, error, isLoading, isValidating } = useConversations({
    page,
    pageSize,
    search: deferredSearch || undefined,
    category: category || undefined,
    remote: remote || undefined,
    clientResponse: clientResponse || undefined,
    match: match || undefined,
  })

  function resetFilters() {
    setSearchInput('')
    setCategory('')
    setRemote('')
    setClientResponse('')
    setMatch('')
    setPage(1)
  }

  const records = data?.data ?? []
  const total = data?.total ?? 0
  const totalPages = data?.total_pages ?? 1

  // Parse chat messages from " | " separated string
  function parseMessages(fullText: string) {
    if (!fullText) return []
    const lines = fullText.split(' | ')
    return lines.map((line, idx) => {
      // Format: [08/03/23 12.57] ROLE: message
      const matchRegex = /^\[([^\]]+)\]\s*([^:]+):\s*(.*)$/.exec(line.trim())
      if (matchRegex) {
        return {
          id: idx,
          timestamp: matchRegex[1],
          role: matchRegex[2].trim().toUpperCase(),
          text: matchRegex[3].trim(),
        }
      }
      return {
        id: idx,
        timestamp: '',
        role: 'CHAT',
        text: line.trim(),
      }
    })
  }

  const kpis: Kpi[] = data
    ? [
        {
          label: 'Total Sub-Percakapan',
          value: formatNumber(total),
          context: 'Unit masalah tersegmentasi',
          icon: MessageSquare,
        },
        {
          label: 'Halaman Aktif',
          value: `${page} / ${totalPages}`,
          context: `Menampilkan ${records.length} item per halaman`,
          icon: SlidersHorizontal,
        },
      ]
    : []

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Master Dataset Percakapan"
        description="Tabel keseluruhan data percakapan WhatsApp lengkap dengan label ground-truth, prediksi AI, status respons, dan remote."
      />

      {/* KPI & Quick Download Bar */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex flex-wrap items-center gap-2">
          <a
            href={getDownloadUrl(sessionId, 'csv')}
            download
            className={cn(buttonVariants({ variant: 'outline', size: 'sm' }), 'gap-1.5')}
          >
            <Download aria-hidden="true" className="size-4 text-emerald-600" />
            <span>Export CSV</span>
          </a>
          <a
            href={getDownloadUrl(sessionId, 'xlsx')}
            download
            className={cn(buttonVariants({ variant: 'outline', size: 'sm' }), 'gap-1.5')}
          >
            <FileSpreadsheet aria-hidden="true" className="size-4 text-emerald-700" />
            <span>Export Excel (.xlsx)</span>
          </a>
        </div>

        <div className="text-xs text-muted-foreground">
          Total Data Terindeks: <span className="font-semibold text-foreground">{formatNumber(total)}</span> Sub-Percakapan
        </div>
      </div>

      {/* Filter and Search Panel */}
      <Panel
        title="Pencarian & Filter Data"
        description="Cari teks percakapan, nama klien, ID, atau saring berdasarkan kategori kendala."
        actions={
          (searchInput || category || remote || clientResponse || match) && (
            <Button variant="ghost" size="sm" onClick={resetFilters} className="text-xs">
              Reset Filter
            </Button>
          )
        }
      >
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5">
          {/* Search Input */}
          <div className="relative">
            <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
            <Input
              type="text"
              placeholder="Cari kata kunci / ID..."
              value={searchInput}
              onChange={(e) => {
                setSearchInput(e.target.value)
                setPage(1)
              }}
              className="pl-8 text-xs"
            />
          </div>

          {/* Category Filter */}
          <select
            value={category}
            onChange={(e) => {
              setCategory(e.target.value)
              setPage(1)
            }}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="">Semua Kategori</option>
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>

          {/* Remote Status Filter */}
          <select
            value={remote}
            onChange={(e) => {
              setRemote(e.target.value)
              setPage(1)
            }}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="">Semua Status Remote</option>
            <option value="REMOTE">REMOTE</option>
            <option value="NON_REMOTE">NON_REMOTE</option>
          </select>

          {/* Client Response Filter */}
          <select
            value={clientResponse}
            onChange={(e) => {
              setClientResponse(e.target.value)
              setPage(1)
            }}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="">Semua Respons</option>
            <option value="RESPONS">RESPONS (Aktif)</option>
            <option value="TIDAK_RESPONS">TIDAK_RESPONS</option>
          </select>

          {/* Match Filter */}
          <select
            value={match}
            onChange={(e) => {
              setMatch(e.target.value)
              setPage(1)
            }}
            className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-xs shadow-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
          >
            <option value="">Semua Status AI Match</option>
            <option value="MATCH">MATCH (Sesuai)</option>
            <option value="DIFFER">DIFFER (Beda)</option>
          </select>
        </div>
      </Panel>

      {/* Main Master Table */}
      <Panel
        title="Tabel Master Percakapan"
        description={`Halaman ${page} dari ${totalPages} (Total ${formatNumber(total)} percakapan)`}
        bodyClassName="p-0"
      >
        <div className="overflow-x-auto">
          <table className="w-full min-w-[1000px] border-collapse text-left text-xs">
            <thead>
              <tr className="border-b bg-muted/40 font-medium text-muted-foreground">
                <th className="px-4 py-3">ID Sub-Conv</th>
                <th className="px-4 py-3">Customer / File</th>
                <th className="px-4 py-3">Waktu Mulai</th>
                <th className="px-4 py-3 text-center">Pesan</th>
                <th className="px-4 py-3 text-center">Respons</th>
                <th className="px-4 py-3 text-center">Remote</th>
                <th className="px-4 py-3">Ground Truth</th>
                <th className="px-4 py-3">Prediksi AI</th>
                <th className="px-4 py-3 text-center">Match</th>
                <th className="px-4 py-3 text-center">Aksi</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {isLoading ? (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center text-muted-foreground">
                    <RefreshCw className="mx-auto mb-2 size-5 animate-spin text-primary" />
                    Memuat data master percakapan...
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={10} className="px-4 py-12 text-center text-muted-foreground">
                    Tidak ada data percakapan yang cocok dengan filter.
                  </td>
                </tr>
              ) : (
                records.map((r) => {
                  const isRemote = r.penanganan_remote === 'REMOTE'
                  const isResp = r.client_response === 'RESPONS'
                  const isMatch = r.prediction_match === 'MATCH'

                  return (
                    <tr key={r.sub_conversation_id} className="transition-colors hover:bg-muted/30">
                      <td className="px-4 py-3 font-mono font-medium text-foreground whitespace-nowrap">
                        {r.sub_conversation_id}
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-foreground">{r.customer}</div>
                        <div className="text-[11px] text-muted-foreground">{r.source_file}</div>
                      </td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{r.start_time}</td>
                      <td className="px-4 py-3 text-center">
                        <span className="font-semibold text-foreground">{r.total_messages}</span>
                        <div className="text-[10px] text-muted-foreground">
                          {r.client_messages_count}C / {r.admin_messages_count}A
                        </div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={cn(
                            'inline-flex items-center rounded-full px-2 py-0.5 text-[10.5px] font-semibold',
                            isResp
                              ? 'bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300'
                              : 'bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400',
                          )}
                        >
                          {r.client_response}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={cn(
                            'inline-flex items-center rounded-full px-2 py-0.5 text-[10.5px] font-semibold',
                            isRemote
                              ? 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300'
                              : 'bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300',
                          )}
                        >
                          {r.penanganan_remote}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium text-foreground">{r.kategori_kendala_ground_truth}</td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-foreground">{r.kategori_kendala_ml_predicted}</div>
                        <div className="text-[10.5px] text-muted-foreground">{r.prediction_confidence} confidence</div>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span
                          className={cn(
                            'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10.5px] font-semibold',
                            isMatch
                              ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300'
                              : 'bg-rose-50 text-rose-700 dark:bg-rose-950 dark:text-rose-300',
                          )}
                        >
                          {isMatch ? <CheckCircle2 className="size-3" /> : <XCircle className="size-3" />}
                          {r.prediction_match}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-center">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedRecord(r)}
                          className="h-7 px-2.5 text-[11px]"
                        >
                          Lihat Chat
                        </Button>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Toolbar */}
        <div className="flex flex-col items-center justify-between gap-3 border-t px-5 py-3 text-xs sm:flex-row">
          <div className="flex items-center gap-2 text-muted-foreground">
            <span>Baris per halaman:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value))
                setPage(1)
              }}
              className="rounded border border-input bg-transparent px-2 py-1 text-xs"
            >
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
            <span>
              Menampilkan {records.length ? (page - 1) * pageSize + 1 : 0} -{' '}
              {Math.min(page * pageSize, total)} dari {formatNumber(total)} data
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1 || isLoading}
              className="h-8 gap-1 px-2.5 text-xs"
            >
              <ChevronLeft className="size-3.5" />
              Sebelumnya
            </Button>
            <span className="px-2 font-medium text-foreground">
              {page} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages || isLoading}
              className="h-8 gap-1 px-2.5 text-xs"
            >
              Berikutnya
              <ChevronRight className="size-3.5" />
            </Button>
          </div>
        </div>
      </Panel>

      {/* Chat Transcript Sheet / Drawer */}
      <Sheet open={!!selectedRecord} onOpenChange={(open) => !open && setSelectedRecord(null)}>
        <SheetContent side="right" className="flex w-full flex-col sm:max-w-xl md:max-w-2xl p-6">
          <SheetHeader className="border-b pb-4">
            <div className="flex items-center justify-between">
              <SheetTitle className="font-mono text-base font-bold text-foreground">
                {selectedRecord?.sub_conversation_id}
              </SheetTitle>
              <span
                className={cn(
                  'rounded-full px-2.5 py-0.5 text-xs font-semibold',
                  selectedRecord?.penanganan_remote === 'REMOTE'
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-slate-100 text-slate-700',
                )}
              >
                {selectedRecord?.penanganan_remote}
              </span>
            </div>
            <SheetDescription className="mt-1 text-xs">
              Klien: <span className="font-medium text-foreground">{selectedRecord?.customer}</span> ({selectedRecord?.source_file}) · Waktu: {selectedRecord?.start_time} - {selectedRecord?.end_time}
            </SheetDescription>
          </SheetHeader>

          {/* Quick Badges in Drawer */}
          {selectedRecord && (
            <div className="my-3 grid grid-cols-2 gap-2 rounded-lg border bg-muted/30 p-3 text-xs sm:grid-cols-4">
              <div>
                <span className="text-muted-foreground">Ground Truth:</span>
                <p className="font-medium text-foreground">{selectedRecord.kategori_kendala_ground_truth}</p>
              </div>
              <div>
                <span className="text-muted-foreground">AI Prediksi:</span>
                <p className="font-medium text-foreground">{selectedRecord.kategori_kendala_ml_predicted}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Confidence:</span>
                <p className="font-medium text-foreground">{selectedRecord.prediction_confidence}</p>
              </div>
              <div>
                <span className="text-muted-foreground">Kredensial / Media:</span>
                <p className="font-medium text-foreground">
                  {selectedRecord.contains_credentials ? 'Ada Password' : 'Tidak Ada'} /{' '}
                  {selectedRecord.has_media ? 'Ada Gambar' : 'Teks Saja'}
                </p>
              </div>
            </div>
          )}

          {/* Messages Bubble List */}
          <div className="flex-1 overflow-y-auto pr-1">
            <div className="flex flex-col gap-3 py-2">
              {selectedRecord &&
                parseMessages(selectedRecord.full_conversation).map((m) => {
                  const isAdmin = m.role === 'ADMIN'
                  const isClient = m.role === 'CLIENT'
                  const isSystem = m.role === 'SYSTEM'

                  if (isSystem) {
                    return (
                      <div key={m.id} className="mx-auto my-1 max-w-[85%] rounded bg-muted/60 px-3 py-1.5 text-center text-[11px] text-muted-foreground">
                        {m.text}
                      </div>
                    )
                  }

                  return (
                    <div
                      key={m.id}
                      className={cn(
                        'flex flex-col max-w-[85%] rounded-lg px-3.5 py-2 text-xs shadow-2xs',
                        isAdmin
                          ? 'ml-auto bg-primary text-primary-foreground items-end rounded-br-none'
                          : 'mr-auto bg-muted/80 text-foreground items-start rounded-bl-none',
                      )}
                    >
                      <div className="flex items-center gap-2 mb-1">
                        <span className={cn('text-[10px] font-bold uppercase tracking-wider', isAdmin ? 'text-primary-foreground/90' : 'text-primary')}>
                          {m.role}
                        </span>
                        {m.timestamp && (
                          <span className={cn('text-[10px]', isAdmin ? 'text-primary-foreground/70' : 'text-muted-foreground')}>
                            {m.timestamp}
                          </span>
                        )}
                      </div>
                      <p className="whitespace-pre-wrap leading-relaxed break-words">{m.text}</p>
                    </div>
                  )
                })}
            </div>
          </div>
        </SheetContent>
      </Sheet>
    </div>
  )
}
