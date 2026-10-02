'use client'

import { createContext, useContext, useEffect, useMemo, useState } from 'react'

export type Dataset =
  | { kind: 'default' }
  | { kind: 'session'; sessionId: string; updatedAt: string }

type DatasetContextValue = {
  dataset: Dataset
  sessionId: string | null
  selectSession: (sessionId: string) => void
  resetToDefault: () => void
}

const DatasetContext = createContext<DatasetContextValue | null>(null)
const SESSION_STORAGE_KEY = 'nlp-zahir-dashboard-session-id'

export function DatasetProvider({ children }: { children: React.ReactNode }) {
  const [dataset, setDataset] = useState<Dataset>({ kind: 'default' })

  useEffect(() => {
    const sessionId = window.sessionStorage.getItem(SESSION_STORAGE_KEY)
    if (sessionId) setDataset({ kind: 'session', sessionId, updatedAt: new Date().toISOString() })
  }, [])

  const value = useMemo<DatasetContextValue>(
    () => ({
      dataset,
      sessionId: dataset.kind === 'session' ? dataset.sessionId : null,
      selectSession: (sessionId) => {
        window.sessionStorage.setItem(SESSION_STORAGE_KEY, sessionId)
        setDataset({ kind: 'session', sessionId, updatedAt: new Date().toISOString() })
      },
      resetToDefault: () => {
        window.sessionStorage.removeItem(SESSION_STORAGE_KEY)
        setDataset({ kind: 'default' })
      },
    }),
    [dataset],
  )

  return <DatasetContext.Provider value={value}>{children}</DatasetContext.Provider>
}

export function useDataset() {
  const context = useContext(DatasetContext)
  if (!context) throw new Error('useDataset must be used within DatasetProvider')
  return context
}
