import { PageSkeleton } from '@/components/shared/skeletons';

export default function Loading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="w-full max-w-7xl">
        <div className="mb-6 flex items-center gap-3">
          <div className="h-8 w-8 animate-pulse rounded-lg bg-primary/20" />
          <div className="h-8 w-64 animate-pulse rounded-lg bg-muted" />
        </div>
        <PageSkeleton />
      </div>
    </div>
  );
}
