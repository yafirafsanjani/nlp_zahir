import { AppSidebar } from '@/components/analytics/sidebar-nav'
import { DatasetProvider } from '@/components/providers/dataset-provider'

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <DatasetProvider>
      <div className="flex min-h-dvh bg-background">
        <AppSidebar />
        <div className="flex min-w-0 flex-1 flex-col">
          <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6 lg:px-10 lg:py-8">{children}</main>
        </div>
      </div>
    </DatasetProvider>
  )
}
