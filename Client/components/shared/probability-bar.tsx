import { cn } from '@/lib/utils';

interface ProbabilityBarProps {
  yesPrice: number;
  noPrice: number;
  className?: string;
  showLabels?: boolean;
  size?: 'sm' | 'md' | 'lg';
}

export function ProbabilityBar({ yesPrice, noPrice, className, showLabels = true, size = 'md' }: ProbabilityBarProps) {
  const heights = { sm: 'h-1.5', md: 'h-2', lg: 'h-3' };
  const total = yesPrice + noPrice;
  const yesPercent = total > 0 ? (yesPrice / total) * 100 : 50;
  return (
    <div className={cn('w-full', className)}>
      {showLabels && (
        <div className="mb-1 flex items-center justify-between text-xs font-medium">
          <span className="text-success">YES {yesPrice.toFixed(0)}%</span>
          <span className="text-destructive">{noPrice.toFixed(0)}% NO</span>
        </div>
      )}
      <div className={cn('flex w-full overflow-hidden rounded-full bg-muted', heights[size])}>
        <div className="bg-success transition-all duration-500 ease-out" style={{ width: `${yesPercent}%` }} />
        <div className="bg-destructive transition-all duration-500 ease-out" style={{ width: `${100 - yesPercent}%` }} />
      </div>
    </div>
  );
}
