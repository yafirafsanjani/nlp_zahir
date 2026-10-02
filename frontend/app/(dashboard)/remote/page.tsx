import type { Metadata } from 'next'
import { RemoteView } from '@/components/views/remote-view'

export const metadata: Metadata = { title: 'Remote Analysis' }

export default function RemotePage() {
  return <RemoteView />
}
