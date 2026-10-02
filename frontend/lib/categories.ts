export const CATEGORIES = [
  'LAINNYA_UNCATEGORIZED',
  'DATABASE_SYSTEM_ERROR',
  'LISENSI_DONGLE_REGISTRASI',
  'INSTALASI_SETUP_NETWORK',
  'LAPORAN_REPORTING',
  'TRANSAKSI_INPUT_DATA',
  'PERTANYAAN_UMUM_FITUR',
  'CUSTOMER_SUPPORT_LAYANAN',
  'ADMINISTRASI_LAYANAN',
] as const

export type Category = (typeof CATEGORIES)[number]

export const ALL_CATEGORIES = 'ALL' as const
export type CategoryFilter = Category | typeof ALL_CATEGORIES

export function isCategory(value: string): value is Category {
  return (CATEGORIES as readonly string[]).includes(value)
}

export const PERIODS = ['daily', 'weekly', 'monthly', 'yearly'] as const
export type Period = (typeof PERIODS)[number]

export const PERIOD_LABELS: Record<Period, string> = {
  daily: 'Daily',
  weekly: 'Weekly',
  monthly: 'Monthly',
  yearly: 'Yearly',
}
