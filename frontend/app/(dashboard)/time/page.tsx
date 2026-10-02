import type { Metadata } from 'next'
import { TimeView } from '@/components/views/time-view'

export const metadata: Metadata = { title: 'Time Analysis' }

export default function TimePage() {
  return <TimeView />
}
