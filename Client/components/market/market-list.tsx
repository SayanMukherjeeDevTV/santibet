import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CategoryBadge } from '@/components/shared/category-badge';
import { StatusBadge } from '@/components/shared/status-badge';
import { Sparkline } from '@/components/shared/sparkline';
import { formatNumber, formatCurrency, getTimeLeft, formatPrice } from '@/lib/format';
import type { Market } from '@/lib/types';
import { Users, TrendingUp } from 'lucide-react';

export function MarketRow({ market, className }: { market: Market; className?: string }) {
  const yes = market.outcomes[0];
  const no = market.outcomes[1];
  const sparkColor = yes.price >= 50 ? 'hsl(142 62% 42%)' : 'hsl(0 72% 51%)';
  return (
    <Link href={`/markets/${market.slug}`} className="block">
      <Card className={cn('flex items-center gap-4 p-4 transition-all hover:border-primary/40 hover:shadow-md', className)}>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2"><CategoryBadge category={market.category} /><StatusBadge status={market.status} /></div>
          <h3 className="mt-2 truncate text-sm font-semibold">{market.question}</h3>
          <div className="mt-1 flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><Users className="h-3 w-3" />{formatNumber(market.traderCount, true)}</span>
            <span className="flex items-center gap-1"><TrendingUp className="h-3 w-3" />{formatCurrency(market.totalVolume, { compact: true })}</span>
            <span>{getTimeLeft(market.endDate)}</span>
          </div>
        </div>
        <Sparkline data={market.sparklineData} color={sparkColor} width={64} height={28} className="hidden sm:block" />
        <div className="hidden items-center gap-4 sm:flex">
          <div className="text-right"><div className="text-xs text-muted-foreground">YES</div><div className="font-semibold text-success tabular-nums">{formatPrice(yes.price)}</div></div>
          <div className="text-right"><div className="text-xs text-muted-foreground">NO</div><div className="font-semibold text-destructive tabular-nums">{formatPrice(no.price)}</div></div>
        </div>
        <Button size="sm" className="shrink-0">Trade</Button>
      </Card>
    </Link>
  );
}

export function MarketList({ markets, className }: { markets: Market[]; className?: string }) {
  return <div className={cn('space-y-2.5', className)}>{markets.map((m) => <MarketRow key={m.id} market={m} />)}</div>;
}
