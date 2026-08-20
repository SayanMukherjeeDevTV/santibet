import { MarketCardGridSkeleton, StatRowSkeleton } from '@/components/shared/skeletons';

export default function Loading() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-8 lg:px-6">
      <div className="h-8 w-48 animate-pulse rounded-lg bg-muted" />
      <StatRowSkeleton count={4} />
      <div className="h-6 w-32 animate-pulse rounded bg-muted" />
      <MarketCardGridSkeleton count={6} />
    </div>
  );
}
