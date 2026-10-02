'use client'

import Link from 'next/link'
import { useRef, useState } from 'react'
import { useSWRConfig } from 'swr'
import { AlertCircle, Check, FileArchive, Loader2, UploadCloud, X } from 'lucide-react'
import { PageHeader } from '@/components/analytics/page-header'
import { Panel } from '@/components/analytics/panel'
import { Button, buttonVariants } from '@/components/ui/button'
import { useDataset } from '@/components/providers/dataset-provider'
import { uploadAndAnalyze, UploadError } from '@/lib/api/client'
import type { AnalyzeResult, UploadStep } from '@/lib/api/types'
import { cn } from '@/lib/utils'

const STEPS: { id: UploadStep; label: string }[] = [
  { id: 'uploading', label: 'Uploading file' },
  { id: 'validating', label: 'Validating ZIP archive' },
  { id: 'processing', label: 'Processing chat data' },
  { id: 'nlp', label: 'Running NLP analysis' },
  { id: 'updating', label: 'Updating analytics' },
  { id: 'completed', label: 'Completed' },
]

const MAX_BYTES = 100 * 1024 * 1024

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

type Status = 'idle' | 'running' | 'done' | 'error'

function StepList({ current, status }: { current: UploadStep | null; status: Status }) {
  const currentIndex = current ? STEPS.findIndex((s) => s.id === current) : -1
  return (
    <ol className="flex flex-col" aria-label="Processing progress">
      {STEPS.map((step, index) => {
        const done = index < currentIndex || (status === 'done' && index <= currentIndex)
        const active = index === currentIndex && status === 'running'
        const failed = index === currentIndex && status === 'error'
        return (
          <li key={step.id} className="flex items-center gap-3 py-2" aria-current={active ? 'step' : undefined}>
            <span
              className={cn(
                'flex size-5 shrink-0 items-center justify-center rounded-full border text-[10px] font-medium tabular-nums',
                done && 'border-foreground bg-foreground text-background',
                active && 'border-primary text-primary',
                failed && 'border-primary bg-primary text-primary-foreground',
                !done && !active && !failed && 'text-muted-foreground',
              )}
            >
              {done ? (
                <Check aria-hidden="true" className="size-3" strokeWidth={3} />
              ) : active ? (
                <Loader2 aria-hidden="true" className="size-3 animate-spin" />
              ) : failed ? (
                <X aria-hidden="true" className="size-3" strokeWidth={3} />
              ) : (
                index + 1
              )}
            </span>
            <span
              className={cn(
                'text-sm',
                done || active || failed ? 'font-medium text-foreground' : 'text-muted-foreground',
              )}
            >
              {step.label}
              <span className="sr-only">{done ? ' (done)' : active ? ' (in progress)' : failed ? ' (failed)' : ''}</span>
            </span>
          </li>
        )
      })}
    </ol>
  )
}

function ResultSummary({ result }: { result: AnalyzeResult }) {
  return (
    <div className="flex flex-col gap-4">
      <dl className="flex flex-col gap-2 text-sm">
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Analysis Status</dt>
          <dd className="text-right font-medium capitalize text-foreground">{result.status}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="text-muted-foreground">Session ID</dt>
          <dd className="font-medium tabular-nums text-foreground">{result.session_id}</dd>
        </div>
        {result.message && <p className="pt-1 text-xs text-muted-foreground">{result.message}</p>}
      </dl>
    </div>
  )
}

export function DataView() {
  const inputRef = useRef<HTMLInputElement>(null)
  const { selectSession } = useDataset()
  const { mutate } = useSWRConfig()
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [status, setStatus] = useState<Status>('idle')
  const [step, setStep] = useState<UploadStep | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<AnalyzeResult | null>(null)

  function choose(next: File | undefined) {
    if (!next || status === 'running') return
    setResult(null)
    setStep(null)
    setStatus('idle')
    if (!next.name.toLowerCase().endsWith('.zip')) {
      setFile(null)
      setError('Only .zip files are supported. Export the WhatsApp chat as a ZIP archive.')
      return
    }
    if (next.size > MAX_BYTES) {
      setFile(null)
      setError(`The file is larger than ${formatBytes(MAX_BYTES)}.`)
      return
    }
    setError(null)
    setFile(next)
  }

  async function start() {
    if (!file) return
    setStatus('running')
    setError(null)
    setResult(null)
    try {
      const analyzed = await uploadAndAnalyze(file, setStep)
      setResult(analyzed)
      setStatus('done')
      selectSession(analyzed.session_id)
      await mutate(() => true)
    } catch (e) {
      setStatus('error')
      setError(e instanceof UploadError ? e.message : 'Upload failed. Check your connection and try again.')
    }
  }

  function reset() {
    setFile(null)
    setStatus('idle')
    setStep(null)
    setError(null)
    setResult(null)
    if (inputRef.current) inputRef.current.value = ''
  }

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Add / Update Data"
        description="Upload a WhatsApp chat export to analyze it and refresh the analytics."
        showActions={false}
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        <Panel title="Upload Dataset" description="ZIP archive exported from WhatsApp" className="lg:col-span-3">
          <div className="flex flex-col gap-4">
            <label
              htmlFor="dataset-file"
              onDragOver={(e) => {
                e.preventDefault()
                setDragging(true)
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(e) => {
                e.preventDefault()
                setDragging(false)
                choose(e.dataTransfer.files[0])
              }}
              className={cn(
                'flex cursor-pointer flex-col items-center justify-center gap-3 rounded-lg border border-dashed px-6 py-12 text-center transition-colors has-[:focus-visible]:ring-3 has-[:focus-visible]:ring-ring',
                dragging ? 'border-primary bg-primary/5' : 'bg-secondary/40 hover:bg-secondary/70',
                status === 'running' && 'pointer-events-none opacity-60',
              )}
            >
              <span className="flex size-10 items-center justify-center rounded-full border bg-background">
                <UploadCloud aria-hidden="true" className="size-4 text-foreground" strokeWidth={1.75} />
              </span>
              <span className="text-sm font-medium text-foreground">
                Drop a ZIP file here, or <span className="text-primary underline underline-offset-4">browse</span>
              </span>
              <span className="text-xs text-muted-foreground">.zip only · up to {formatBytes(MAX_BYTES)}</span>
              <input
                ref={inputRef}
                id="dataset-file"
                type="file"
                accept=".zip,application/zip,application/x-zip-compressed"
                className="sr-only"
                disabled={status === 'running'}
                onChange={(e) => choose(e.target.files?.[0])}
              />
            </label>

            {file && (
              <div className="flex items-center gap-3 rounded-md border px-3 py-2.5">
                <FileArchive aria-hidden="true" className="size-4 shrink-0 text-muted-foreground" strokeWidth={1.75} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-foreground">{file.name}</p>
                  <p className="text-xs text-muted-foreground tabular-nums">{formatBytes(file.size)}</p>
                </div>
                {status !== 'running' && (
                  <Button variant="ghost" size="icon-sm" onClick={reset} aria-label="Remove selected file">
                    <X aria-hidden="true" />
                  </Button>
                )}
              </div>
            )}

            {error && (
              <div role="alert" className="flex items-start gap-2 rounded-md border border-primary/30 bg-primary/5 px-3 py-2.5">
                <AlertCircle aria-hidden="true" className="mt-0.5 size-4 shrink-0 text-primary" />
                <p className="text-sm text-foreground">{error}</p>
              </div>
            )}

            <div className="flex flex-wrap items-center gap-2">
              <Button onClick={start} disabled={!file || status === 'running' || status === 'done'}>
                {status === 'running' ? (
                  <Loader2 aria-hidden="true" className="animate-spin" />
                ) : (
                  <UploadCloud aria-hidden="true" />
                )}
                {status === 'running' ? 'Analyzing…' : status === 'error' ? 'Retry Upload' : 'Upload and Analyze'}
              </Button>
              {status === 'done' && (
                <Button variant="outline" onClick={reset}>
                  Upload another file
                </Button>
              )}
            </div>
          </div>
        </Panel>

        <Panel
          title={result ? 'Analysis Complete' : 'Processing Status'}
          description={result ? 'The new dataset is now active' : 'Steps run after you start the upload'}
          className="lg:col-span-2"
        >
          <div aria-live="polite" className="flex flex-col gap-5">
            {result ? (
              <>
                <ResultSummary result={result} />
                <Link href="/" className={buttonVariants({ className: 'w-full' })}>
                  View updated analytics
                </Link>
              </>
            ) : (
              <StepList current={step} status={status} />
            )}
          </div>
        </Panel>
      </div>
    </div>
  )
}
