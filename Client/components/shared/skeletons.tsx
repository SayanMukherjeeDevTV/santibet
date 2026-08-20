import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export function MarketCardSkeleton() {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between"><Skeleton className="h-5 w-20" /><Skeleton className="h-5 w-16" /></div>
      <Skeleton className="mt-4 h-12 w-full" />
      <div className="mt-4 flex items-center gap-3"><Skeleton className="h-3 flex-1" /><Skeleton className="h-3 w-20" /></div>
      <Skeleton className="mt-3 h-2 w-full rounded-full" />
      <div className="mt-4 flex items-center justify-between"><Skeleton className="h-4 w-24" /><Skeleton className="h-8 w-20 rounded-lg" /></div>
    </Card>
  );
}

export function MarketCardGridSkeleton({ count = 6 }: { count?: number }) {
  return <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{Array.from({ length: count }).map((_, i) => <MarketCardSkeleton key={i} />)}</div>;
}

export function StatCardSkeleton() {
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between">
        <div className="flex-1"><Skeleton className="h-4 w-24" /><Skeleton className="mt-2 h-8 w-32" /><Skeleton className="mt-2 h-3 w-28" /></div>
        <Skeleton className="h-10 w-10 rounded-lg" />
      </div>
    </Card>
  );
}

export function StatRowSkeleton({ count = 4 }: { count?: number }) {
  return <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">{Array.from({ length: count }).map((_, i) => <StatCardSkeleton key={i} />)}</div>;
}

export function ChartSkeleton({ className }: { className?: string }) {
  return (
    <Card className={cn('p-5', className)}>
      <div className="flex items-center justify-between"><Skeleton className="h-5 w-32" /><Skeleton className="h-5 w-20" /></div>
      <Skeleton className="mt-4 h-[260px] w-full rounded-lg" />
    </Card>
  );
}

export function TableSkeleton({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <Card className="p-0">
      <div className="border-b p-4"><Skeleton className="h-5 w-40" /></div>
      <div className="divide-y">
        {Array.from({ length: rows }).map((_, r) => (
          <div key={r} className="flex items-center gap-4 p-4">
            {Array.from({ length: cols }).map((_, c) => <Skeleton key={c} className="h-4 flex-1" />)}
          </div>
        ))}
      </div>
    </Card>
  );
}

export function ListSkeleton({ count = 5, className }: { count?: number; className?: string }) {
  return (
    <div className={cn('space-y-3', className)}>
      {Array.from({ length: count }).map((_, i) => (
        <Card key={i} className="flex items-center gap-4 p-4">
          <Skeleton className="h-10 w-10 rounded-full" />
          <div className="flex-1"><Skeleton className="h-4 w-48" /><Skeleton className="mt-2 h-3 w-32" /></div>
          <Skeleton className="h-6 w-20" />
        </Card>
      ))}
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="space-y-6 p-6">
      <Skeleton className="h-8 w-64" />
      <StatRowSkeleton />
      <div className="grid gap-4 lg:grid-cols-3">
        <ChartSkeleton className="lg:col-span-2" />
        <Card className="p-5"><Skeleton className="h-5 w-24" /><div className="mt-4 space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-16 w-full rounded-lg" />)}</div></Card>
      </div>
    </div>
  );
}
