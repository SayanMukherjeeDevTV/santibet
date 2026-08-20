'use client';

import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Search, LayoutGrid, List, SlidersHorizontal } from 'lucide-react';

export type SortOption = 'volume' | 'traders' | 'ending-soon' | 'newest';
export type ViewMode = 'grid' | 'list';

export function MarketFilters({ search, onSearchChange, sort, onSortChange, status, onStatusChange, view, onViewChange, className }: {
  search: string; onSearchChange: (v: string) => void; sort: SortOption; onSortChange: (v: SortOption) => void;
  status: string; onStatusChange: (v: string) => void; view: ViewMode; onViewChange: (v: ViewMode) => void; className?: string;
}) {
  return (
    <div className={cn('flex flex-col gap-3 sm:flex-row sm:items-center', className)}>
      <div className="relative flex-1">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search markets..." value={search} onChange={(e) => onSearchChange(e.target.value)} className="pl-9" />
      </div>
      <div className="flex items-center gap-2">
        <Select value={status} onValueChange={onStatusChange}>
          <SelectTrigger className="w-[130px]"><SlidersHorizontal className="h-3.5 w-3.5" /><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="all">All Status</SelectItem><SelectItem value="active">Active</SelectItem><SelectItem value="upcoming">Upcoming</SelectItem><SelectItem value="resolved">Resolved</SelectItem></SelectContent>
        </Select>
        <Select value={sort} onValueChange={(v) => onSortChange(v as SortOption)}>
          <SelectTrigger className="w-[150px]"><SelectValue /></SelectTrigger>
          <SelectContent><SelectItem value="volume">Highest Volume</SelectItem><SelectItem value="traders">Most Traders</SelectItem><SelectItem value="ending-soon">Ending Soon</SelectItem><SelectItem value="newest">Newest</SelectItem></SelectContent>
        </Select>
        <div className="flex items-center rounded-lg border border-border">
          <Button variant={view === 'grid' ? 'secondary' : 'ghost'} size="icon" className="h-9 w-9 rounded-r-none" onClick={() => onViewChange('grid')}><LayoutGrid className="h-4 w-4" /></Button>
          <Button variant={view === 'list' ? 'secondary' : 'ghost'} size="icon" className="h-9 w-9 rounded-l-none" onClick={() => onViewChange('list')}><List className="h-4 w-4" /></Button>
        </div>
      </div>
    </div>
  );
}
