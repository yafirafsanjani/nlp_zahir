import type { Metadata } from 'next'
import { DataView } from '@/components/views/data-view'

export const metadata: Metadata = { title: 'Add / Update Data' }

export default function DataPage() {
  return <DataView />
}
