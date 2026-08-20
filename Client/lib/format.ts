export function formatCurrency(value: number, options: { compact?: boolean; decimals?: number } = {}): string {
  const { compact = false, decimals } = options;
  if (compact && Math.abs(value) >= 1000) {
    return new Intl.NumberFormat('en-US', {
      style: 'currency', currency: 'USD', notation: 'compact', maximumFractionDigits: 1,
    }).format(value);
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD',
    minimumFractionDigits: decimals ?? 2, maximumFractionDigits: decimals ?? 2,
  }).format(value);
}

export function formatNumber(value: number, compact = false): string {
  return new Intl.NumberFormat('en-US', {
    notation: compact ? 'compact' : 'standard', maximumFractionDigits: 1,
  }).format(value);
}

export function formatPercent(value: number, decimals = 1): string {
  return `${value > 0 ? '+' : ''}${value.toFixed(decimals)}%`;
}

export function formatPrice(value: number): string {
  return `${value.toFixed(2)}\u00A2`;
}

export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', year: 'numeric' }).format(new Date(date));
}

export function formatDateTime(date: string | Date): string {
  return new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' }).format(new Date(date));
}

export function formatRelativeTime(date: string | Date): string {
  const diff = new Date(date).getTime() - Date.now();
  const absDiff = Math.abs(diff);
  const past = diff < 0;
  const mins = Math.floor(absDiff / 60000);
  const hours = Math.floor(absDiff / 3600000);
  const days = Math.floor(absDiff / 86400000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${past ? mins + 'm ago' : 'in ' + mins + 'm'}`;
  if (hours < 24) return `${past ? hours + 'h ago' : 'in ' + hours + 'h'}`;
  if (days < 30) return `${past ? days + 'd ago' : 'in ' + days + 'd'}`;
  return formatDate(date);
}

export function getTimeLeft(endDate: string): string {
  const diff = new Date(endDate).getTime() - Date.now();
  if (diff <= 0) return 'Ended';
  const days = Math.floor(diff / 86400000);
  const hours = Math.floor((diff % 86400000) / 3600000);
  if (days > 0) return `${days}d ${hours}h left`;
  const mins = Math.floor((diff % 3600000) / 60000);
  return `${hours}h ${mins}m left`;
}

export function getInitials(name: string): string {
  return name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase();
}
