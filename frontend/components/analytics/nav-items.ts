import {
  CalendarRange,
  Headset,
  LayoutGrid,
  ListTree,
  UploadCloud,
  Users,
  type LucideIcon,
} from 'lucide-react'

export type NavItem = { href: string; label: string; icon: LucideIcon }

export const ANALYSIS_NAV: NavItem[] = [
  { href: '/', label: 'Overview', icon: LayoutGrid },
  { href: '/issues', label: 'Issue Analysis', icon: ListTree },
  { href: '/remote', label: 'Remote Analysis', icon: Headset },
  { href: '/customers', label: 'Customer Analysis', icon: Users },
  { href: '/time', label: 'Time Analysis', icon: CalendarRange },
]

export const DATA_NAV: NavItem[] = [
  { href: '/data', label: 'Add / Update Data', icon: UploadCloud },
]
