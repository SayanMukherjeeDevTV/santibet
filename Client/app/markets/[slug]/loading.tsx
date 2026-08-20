import { ChartSkeleton, StatCardSkeleton } from '@/components/shared/skeletons';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

export default function Loading() {
  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-6 lg:px-6">
      <Skeleton className="h-4 w-32" />
      <div className="space-y-4">
        <Skeleton className="h-8 w-3/4" />
        <div className="flex gap-4">
          <Skeleton className="h-4 w-32" /><Skeleton className="h-4 w-32" /><Skeleton className="h-4 w-32" />
        </div>
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <ChartSkeleton />
          <Card className="p-5"><Skeleton className="h-5 w-40" /><Skeleton className="mt-4 h-12 w-full" /></Card>
        </div>
        <div className="space-y-6">
          <Card className="p-5"><Skeleton className="h-5 w-20" /><div className="mt-4 space-y-3"><Skeleton className="h-10 w-full" /><Skeleton className="h-32 w-full" /></div></Card>
        </div>
      </div>
    </div>
  );
}
