import { MarketCardGridSkeleton, StatRowSkeleton } from '@/components/shared/skeletons';
import { Skeleton } from '@/components/ui/skeleton';

export default function Loading() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 lg:px-6">
      <div className="h-8 w-64 animate-pulse rounded-lg bg-muted" />
      <StatRowSkeleton count={4} />
      <Skeleton className="h-24 w-full rounded-xl" />
      <MarketCardGridSkeleton count={3} />
    </div>
  );
}
