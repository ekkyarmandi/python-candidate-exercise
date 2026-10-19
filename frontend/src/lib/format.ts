const MONEY = new Intl.NumberFormat(undefined, { maximumFractionDigits: 2 })
const DATE_TIME = new Intl.DateTimeFormat(undefined, {
  dateStyle: 'medium',
  timeStyle: 'short',
})

export function formatMoney(value: number): string {
  return '$' + MONEY.format(Number(value) || 0)
}

export function formatDate(iso: string): string {
  if (!iso) return ''
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? '' : DATE_TIME.format(date)
}
