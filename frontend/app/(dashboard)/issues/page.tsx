import type { Metadata } from 'next'
import { IssuesView } from '@/components/views/issues-view'

export const metadata: Metadata = { title: 'Issue Analysis' }

export default function IssuesPage() {
  return <IssuesView />
}
