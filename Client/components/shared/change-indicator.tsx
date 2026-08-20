import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown } from 'lucide-react';

export function ChangeIndicator({ value, showIcon = true, className, suffix = '%' }: { value: number; showIcon?: boolean; className?: string; suffix?: string }) {
  const positive = value >= 0;
  return (
    <span className={cn('inline-flex items-center gap-0.5 font-medium tabular-nums', positive ? 'text-success' : 'text-destructive', className)}>
      {showIcon && (positive ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />)}
      {positive ? '+' : ''}{value.toFixed(1)}{suffix}
    </span>
  );
}
