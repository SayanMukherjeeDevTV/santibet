import { cn } from '@/lib/utils';
import type { MarketStatus } from '@/lib/types';
import { Clock, CheckCircle, Flame } from 'lucide-react';

export function StatusBadge({ status, className }: { status: MarketStatus; className?: string }) {
  const config = {
    active: { label: 'Active', icon: Flame, className: 'bg-success/15 text-success border-success/20' },
    upcoming: { label: 'Upcoming', icon: Clock, className: 'bg-warning/15 text-warning border-warning/20' },
    resolved: { label: 'Resolved', icon: CheckCircle, className: 'bg-muted text-muted-foreground border-border' },
  };
  const { label, icon: Icon, className: badgeClass } = config[status];
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium', badgeClass, className)}>
      <Icon className="h-3 w-3" />
      {label}
    </span>
  );
}
