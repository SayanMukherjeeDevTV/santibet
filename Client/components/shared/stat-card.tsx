import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { ArrowDownRight, ArrowUpRight } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string;
  change?: number;
  icon: LucideIcon;
  className?: string;
  iconColor?: string;
}

export function StatCard({ label, value, change, icon: Icon, className, iconColor = 'text-primary' }: StatCardProps) {
  return (
    <Card className={cn('p-5', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="mt-2 font-display text-2xl font-bold tracking-tight">{value}</p>
          {change !== undefined && (
            <div className="mt-2 flex items-center gap-1 text-xs">
              {change >= 0 ? <ArrowUpRight className="h-3.5 w-3.5 text-success" /> : <ArrowDownRight className="h-3.5 w-3.5 text-destructive" />}
              <span className={change >= 0 ? 'text-success' : 'text-destructive'}>{Math.abs(change).toFixed(1)}%</span>
              <span className="text-muted-foreground">vs last period</span>
            </div>
          )}
        </div>
        <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10', iconColor)}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
    </Card>
  );
}
