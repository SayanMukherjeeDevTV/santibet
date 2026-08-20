import { MarketCard } from '@/components/market/market-card';
import { MarketCardGridSkeleton } from '@/components/shared/skeletons';
import type { Market } from '@/lib/types';

export function MarketGrid({ markets, loading, columns = 3 }: { markets: Market[]; loading?: boolean; columns?: 2 | 3 | 4 }) {
  if (loading) return <MarketCardGridSkeleton count={columns * 2} />;
  const gridCols = { 2: 'sm:grid-cols-2', 3: 'sm:grid-cols-2 lg:grid-cols-3', 4: 'sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4' }[columns];
  return <div className={`grid gap-4 ${gridCols}`}>{markets.map((market) => <MarketCard key={market.id} market={market} />)}</div>;
}
