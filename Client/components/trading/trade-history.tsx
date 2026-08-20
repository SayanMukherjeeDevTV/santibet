'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { formatPrice, formatNumber, formatRelativeTime } from '@/lib/format';
import { fetchTradeHistory } from '@/lib/api';
import type { TradeHistoryEntry } from '@/lib/types';

export function TradeHistory({ slug }: { slug: string }) {
  const [trades, setTrades] = React.useState<TradeHistoryEntry[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const data = await fetchTradeHistory(slug);
        if (mounted) setTrades(data || []);
      } catch (err) {
        console.error(err);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 5000); // Polling every 5s
    return () => { mounted = false; clearInterval(interval); };
  }, [slug]);

  return (
    <Card className="p-5">
      <h3 className="mb-4 font-semibold">Recent Trades</h3>
      <div className="mb-2 grid grid-cols-4 text-xs font-medium text-muted-foreground"><span>Side</span><span className="text-right">Price</span><span className="text-right">Size</span><span className="text-right">Time</span></div>
      <div className="max-h-[280px] space-y-0.5 overflow-y-auto scrollbar-thin">
        {loading && trades.length === 0 ? (
          <div className="text-xs text-muted-foreground text-center py-4">Loading trades...</div>
        ) : trades.length === 0 ? (
          <div className="text-xs text-muted-foreground text-center py-4">No recent trades</div>
        ) : (
          trades.map((t) => (
            <div key={t.id} className="grid grid-cols-4 rounded px-1 py-1 text-sm tabular-nums hover:bg-muted/50">
              <span className={cn('font-medium', t.side === 'buy' ? 'text-success' : 'text-destructive')}>{t.side === 'buy' ? 'BUY' : 'SELL'} {t.outcome}</span>
              <span className="text-right">{formatPrice(t.price)}</span>
              <span className="text-right">{formatNumber(t.size)}</span>
              <span className="text-right text-xs text-muted-foreground">{formatRelativeTime(t.time)}</span>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
