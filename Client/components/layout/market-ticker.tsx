'use client';

import Link from 'next/link';
import { markets } from '@/lib/mock-data';
import { formatPrice } from '@/lib/format';
import { TrendingUp, TrendingDown } from 'lucide-react';

export function MarketTicker() {
  const tickerMarkets = markets.slice(0, 8);
  const items = [...tickerMarkets, ...tickerMarkets];
  return (
    <div className="border-b border-border bg-card/50 py-2">
      <div className="flex items-center gap-2 overflow-hidden">
        <div className="flex shrink-0 items-center gap-1.5 pl-4 text-xs font-bold text-primary">
          <span className="relative flex h-2 w-2">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex h-2 w-2 rounded-full bg-primary" />
          </span>
          LIVE
        </div>
        <div className="flex animate-ticker items-center gap-6 whitespace-nowrap">
          {items.map((m, i) => {
            const yes = m.outcomes[0];
            const prev = m.priceHistory[m.priceHistory.length - 2]?.yes ?? yes.price;
            const change = yes.price - prev;
            const positive = change >= 0;
            return (
              <Link key={`${m.id}-${i}`} href={`/markets/${m.slug}`} className="flex items-center gap-2 text-sm transition-colors hover:text-primary">
                <span className="max-w-[200px] truncate text-muted-foreground">{m.question}</span>
                <span className="font-medium tabular-nums" suppressHydrationWarning>{formatPrice(yes.price)}</span>
                <span className={`flex items-center gap-0.5 text-xs ${positive ? 'text-success' : 'text-destructive'}`} suppressHydrationWarning>
                  {positive ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                  {positive ? '+' : ''}{change.toFixed(1)}
                </span>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}