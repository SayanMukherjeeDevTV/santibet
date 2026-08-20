'use client';

import { cn } from '@/lib/utils';
import { categories } from '@/lib/mock-data';
import type { MarketCategory } from '@/lib/types';
import * as Icons from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export function CategoryFilter({ selected, onChange, className, variant = 'pills' }: {
  selected: MarketCategory | 'all'; onChange: (value: MarketCategory | 'all') => void; className?: string; variant?: 'pills' | 'cards';
}) {
  if (variant === 'cards') {
    return (
      <div className={cn('grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7', className)}>
        {categories.map((cat) => {
          const Icon = (Icons as unknown as Record<string, LucideIcon>)[cat.icon] ?? Icons.Globe;
          const active = selected === cat.id;
          return (
            <button key={cat.id} onClick={() => onChange(active ? 'all' : (cat.id as MarketCategory))} className={cn('flex flex-col items-center gap-2 rounded-xl border p-4 transition-all', active ? 'border-primary bg-primary/5 shadow-sm' : 'border-border hover:border-foreground/20')}>
              <div className={cn('flex h-10 w-10 items-center justify-center rounded-lg', active ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground')}><Icon className="h-5 w-5" /></div>
              <span className="text-xs font-medium">{cat.label}</span>
            </button>
          );
        })}
      </div>
    );
  }
  return (
    <div className={cn('flex flex-wrap items-center gap-2', className)}>
      <button onClick={() => onChange('all')} className={cn('rounded-full px-3 py-1.5 text-sm font-medium transition-colors', selected === 'all' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground hover:bg-secondary/70')}>All</button>
      {categories.map((cat) => {
        const Icon = (Icons as unknown as Record<string, LucideIcon>)[cat.icon] ?? Icons.Globe;
        const active = selected === cat.id;
        return <button key={cat.id} onClick={() => onChange(active ? 'all' : (cat.id as MarketCategory))} className={cn('flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-colors', active ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground hover:bg-secondary/70')}><Icon className="h-3.5 w-3.5" />{cat.label}</button>;
      })}
    </div>
  );
}
