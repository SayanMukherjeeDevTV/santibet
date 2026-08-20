import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CategoryBadge } from '@/components/shared/category-badge';
import { ProbabilityBar } from '@/components/shared/probability-bar';
import { Sparkline } from '@/components/shared/sparkline';
import { formatNumber, formatCurrency, getTimeLeft, formatPrice } from '@/lib/format';
import type { Market } from '@/lib/types';
import { ArrowRight, Flame, Users } from 'lucide-react';

export function FeaturedMarket({ market, className }: { market: Market; className?: string }) {
  const yes = market.outcomes[0];
  const no = market.outcomes[1];
  return (
    <Card className={cn('relative overflow-hidden p-0', className)}>
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-chart-2/5" />
      <div className="absolute right-0 top-0 h-32 w-32 rounded-full bg-primary/10 blur-3xl" />
      <div className="relative p-6">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-bold text-primary"><Flame className="h-3 w-3" /> FEATURED</span>
          <CategoryBadge category={market.category} />
        </div>
        <h2 className="mt-4 text-xl font-bold leading-tight sm:text-2xl">{market.question}</h2>
        <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">{market.description}</p>
        <div className="mt-5">
          <div className="mb-2 flex items-baseline justify-between">
            <span className="text-3xl font-bold tabular-nums text-success">{formatPrice(yes.price)}</span>
            <span className="text-sm text-muted-foreground">{getTimeLeft(market.endDate)}</span>
          </div>
          <ProbabilityBar yesPrice={yes.price} noPrice={no.price} size="lg" />
        </div>
        <div className="mt-5 flex items-center gap-6 text-sm">
          <div><div className="flex items-center gap-1 text-muted-foreground"><Users className="h-3.5 w-3.5" /> Traders</div><div className="mt-0.5 font-semibold">{formatNumber(market.traderCount, true)}</div></div>
          <div><div className="text-muted-foreground">Volume</div><div className="mt-0.5 font-semibold">{formatCurrency(market.totalVolume, { compact: true })}</div></div>
          <div className="ml-auto"><Sparkline data={market.sparklineData} width={80} height={36} /></div>
        </div>
        <div className="mt-5 flex gap-3">
          <Button asChild className="flex-1"><Link href={`/markets/${market.slug}`}>Trade Now <ArrowRight className="ml-1 h-4 w-4" /></Link></Button>
          <Button variant="outline" asChild><Link href={`/markets/${market.slug}`}>Details</Link></Button>
        </div>
      </div>
    </Card>
  );
}
