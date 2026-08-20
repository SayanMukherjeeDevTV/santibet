'use client';

import * as React from 'react';
import { SiteLayout } from '@/components/layout/site-layout';
import { MarketGrid } from '@/components/market/market-grid';
import { MarketList } from '@/components/market/market-list';
import { MarketFilters, type SortOption, type ViewMode } from '@/components/market/market-filters';
import { CategoryFilter } from '@/components/market/category-filter';
import { MarketCardGridSkeleton, ListSkeleton } from '@/components/shared/skeletons';
import { fetchMarkets } from '@/lib/api';
import type { MarketCategory, Market } from '@/lib/types';
import { BarChart3 } from 'lucide-react';

export default function MarketsPage() {
  const [search, setSearch] = React.useState('');
  const [category, setCategory] = React.useState<MarketCategory | 'all'>('all');
  const [sort, setSort] = React.useState<SortOption>('volume');
  const [status, setStatus] = React.useState('all');
  const [view, setView] = React.useState<ViewMode>('grid');
  const [loading, setLoading] = React.useState(true);
  const [filtered, setFiltered] = React.useState<Market[]>([]);
  const [totalCount, setTotalCount] = React.useState<number>(0);

  React.useEffect(() => {
    let active = true;
    setLoading(true);
    
    const params: Record<string, string> = {};
    if (category !== 'all') params.category = category;
    if (status !== 'all') params.status = status;
    if (search) params.search = search;
    if (sort) {
      if (sort === 'volume') params.sort = 'newest'; // Fallback if backend doesn't fully support volume sorting
      else if (sort === 'ending-soon') params.sort = 'ending_soon';
      else params.sort = sort;
    }

    fetchMarkets(params)
      .then(data => {
        if (active) {
          setFiltered(data.items || []);
          setTotalCount(data.total || 0);
          setLoading(false);
        }
      })
      .catch(err => {
        console.error('Failed to fetch markets:', err);
        if (active) {
          setFiltered([]);
          setLoading(false);
        }
      });

    return () => { active = false; };
  }, [search, category, sort, status]);

  return (
    <SiteLayout>
      <div className="mx-auto max-w-7xl px-4 py-8 lg:px-6">
        <div className="mb-6">
          <div className="flex items-center gap-2"><BarChart3 className="h-6 w-6 text-primary" /><h1 className="font-display text-3xl font-bold">All Markets</h1></div>
          <p className="mt-1 text-muted-foreground">Trade on {totalCount > 0 ? totalCount : 'our'} active prediction markets across all categories</p>
        </div>
        <CategoryFilter selected={category} onChange={setCategory} variant="pills" className="mb-4" />
        <MarketFilters search={search} onSearchChange={setSearch} sort={sort} onSortChange={setSort} status={status} onStatusChange={setStatus} view={view} onViewChange={setView} className="mb-6" />
        {loading ? (view === 'grid' ? <MarketCardGridSkeleton count={9} /> : <ListSkeleton count={6} />) : filtered.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-border py-20 text-center">
            <p className="text-lg font-medium">No markets found</p><p className="mt-1 text-sm text-muted-foreground">Try adjusting your filters or search query</p>
          </div>
        ) : (
          <><p className="mb-4 text-sm text-muted-foreground">{filtered.length} market{filtered.length !== 1 ? 's' : ''}</p>{view === 'grid' ? <MarketGrid markets={filtered} /> : <MarketList markets={filtered} />}</>
        )}
      </div>
    </SiteLayout>
  );
}
