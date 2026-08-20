'use client';

import * as React from 'react';
import { Card } from '@/components/ui/card';
import { formatPrice, formatNumber } from '@/lib/format';
import { fetchOrderBook } from '@/lib/api';

export function OrderBook({ slug }: { slug: string }) {
  const [bids, setBids] = React.useState<any[]>([]);
  const [asks, setAsks] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const data = await fetchOrderBook(slug, 'YES');
        if (mounted) {
          setBids(data.bids || []);
          setAsks(data.asks || []);
        }
      } catch (err) {
        console.error(err);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    load();
    const interval = setInterval(load, 10000); // Polling every 10s
    return () => { mounted = false; clearInterval(interval); };
  }, [slug]);

  if (loading) {
    return <Card className="p-5 flex justify-center text-sm text-muted-foreground"><div className="py-4">Loading order book...</div></Card>;
  }

  // The UI mock had "yes" and "no" sides. In our backend, bids = buying YES, asks = selling YES (buying NO)
  const bookSides = [
    { label: 'yes', entries: bids, colorClass: 'text-success', bgClass: 'bg-success/10', alignClass: 'right-0' },
    { label: 'no', entries: asks, colorClass: 'text-destructive', bgClass: 'bg-destructive/10', alignClass: 'left-0' }
  ];

  return (
    <Card className="p-5">
      <h3 className="mb-4 font-semibold">Order Book</h3>
      <div className="grid grid-cols-2 gap-4">
        {bookSides.map((side) => {
          const maxTotal = side.entries.length > 0 ? Math.max(...side.entries.map(e => e.total)) : 1;
          
          return (
            <div key={side.label}>
              <div className="mb-2 grid grid-cols-3 text-xs font-medium text-muted-foreground"><span>Price</span><span className="text-right">Size</span><span className="text-right">Total</span></div>
              <div className="space-y-0.5">
                {side.entries.length === 0 ? (
                  <div className="text-xs text-muted-foreground text-center py-2">No orders</div>
                ) : (
                  side.entries.map((entry, i) => (
                    <div key={i} className="relative grid grid-cols-3 rounded px-1 py-0.5 text-sm tabular-nums">
                      <div className={`absolute inset-y-0 ${side.alignClass} rounded ${side.bgClass}`} style={{ width: `${Math.min(100, (entry.total / maxTotal) * 100)}%` }} />
                      <span className={`relative ${side.colorClass}`}>{formatPrice(entry.price)}</span>
                      <span className="relative text-right">{formatNumber(entry.size)}</span>
                      <span className="relative text-right text-muted-foreground">{formatNumber(entry.total)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
