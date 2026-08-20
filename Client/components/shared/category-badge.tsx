import { cn } from '@/lib/utils';
import { categories } from '@/lib/mock-data';
import type { MarketCategory } from '@/lib/types';
import * as Icons from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export function CategoryBadge({ category, className, size = 'sm' }: { category: MarketCategory; className?: string; size?: 'sm' | 'md' }) {
  const info = categories.find((c) => c.id === category);
  if (!info) return null;
  const Icon = (Icons as unknown as Record<string, LucideIcon>)[info.icon] ?? Icons.Globe;
  return (
    <span className={cn('inline-flex items-center gap-1.5 rounded-full font-medium', size === 'sm' ? 'px-2.5 py-0.5 text-xs' : 'px-3 py-1 text-sm', 'bg-secondary text-secondary-foreground', className)}>
      <Icon className={size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'} />
      {info.label}
    </span>
  );
}
