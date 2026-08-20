import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ProbabilityBar } from '@/components/shared/probability-bar';
import { CategoryBadge } from '@/components/shared/category-badge';
import { StatusBadge } from '@/components/shared/status-badge';
import { Sparkline } from '@/components/shared/sparkline';
import { formatNumber, formatCurrency, getTimeLeft, formatPrice } from '@/lib/format';
import type { Market } from '@/lib/types';
import { Users, TrendingUp } from 'lucide-react';

export function MarketCard({ market, className }: { market: Market; className?: string }) {
  const yes = market.outcomes[0];
  const no = market.outcomes[1];
  const sparkColor = yes.price >= 50 ? 'hsl(142 62% 42%)' : 'hsl(0 72% 51%)';
  return (
    <Link href={`/markets/${market.slug}`} className="block">
      <Card className={cn('group relative overflow-hidden p-5 transition-all duration-200 hover:border-primary/40 hover:shadow-lg', className)}>
        <div className="flex items-start justify-between gap-2"><CategoryBadge category={market.category} /><StatusBadge status={market.status} /></div>
        <h3 className="mt-3 line-clamp-2 min-h-[2.5rem] text-sm font-semibold leading-snug">{market.question}</h3>
        <div className="mt-3 flex items-center gap-3">
          <div className="flex-1"><ProbabilityBar yesPrice={yes.price} noPrice={no.price} size="sm" /></div>
          <Sparkline data={market.sparklineData} color={sparkColor} width={56} height={24} />
        </div>
        <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><Users className="h-3 w-3" />{formatNumber(market.traderCount, true)} traders</span>
          <span className="flex items-center gap-1"><TrendingUp className="h-3 w-3" />{formatCurrency(market.volume24h, { compact: true })} 24h</span>
          <span className="font-medium text-foreground/70">{getTimeLeft(market.endDate)}</span>
        </div>
        <div className="mt-4 flex gap-2">
          <Button size="sm" className="flex-1 bg-success/90 text-success-foreground hover:bg-success">Yes {formatPrice(yes.price)}</Button>
          <Button size="sm" variant="secondary" className="flex-1 bg-destructive/90 text-destructive-foreground hover:bg-destructive">No {formatPrice(no.price)}</Button>
        </div>
      </Card>
    </Link>
  );
}
