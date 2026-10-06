import type { Metadata } from 'next'
import { ConversationsView } from '@/components/views/conversations-view'

export const metadata: Metadata = { title: 'Master Conversations' }

export default function ConversationsPage() {
  return <ConversationsView />
}
