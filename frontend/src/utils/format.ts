import { format, formatDistanceToNow } from 'date-fns'

export function formatCurrency(value: number, currency = 'USD'): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`
}

export function formatNumber(value: number, decimals = 2): string {
  return value.toFixed(decimals)
}

export function formatDate(date: string | Date): string {
  return format(new Date(date), 'MMM d, yyyy')
}

export function formatDateTime(date: string | Date): string {
  return format(new Date(date), 'MMM d, yyyy HH:mm')
}

export function formatTimeAgo(date: string | Date): string {
  return formatDistanceToNow(new Date(date), { addSuffix: true })
}

export function formatPrice(price: number, symbol: string): string {
  // Determine decimal places based on symbol
  const digits = getSymbolDigits(symbol)
  return price.toFixed(digits)
}

export function getSymbolDigits(symbol: string): number {
  const upperSymbol = symbol.toUpperCase()

  // JPY pairs have 3 digits (2 for JPY cross + 1)
  if (upperSymbol.includes('JPY')) {
    return 3
  }

  // Gold and metals often have 2 digits
  if (upperSymbol.includes('XAU') || upperSymbol === 'GOLD') {
    return 2
  }

  // Indices
  if (['US30', 'US100', 'US500', 'NAS100', 'DJ30', 'GER40', 'UK100'].some(i => upperSymbol.includes(i))) {
    return 1
  }

  // Default forex pairs
  return 5
}

export function formatVolume(volume: number): string {
  return volume.toFixed(2)
}
