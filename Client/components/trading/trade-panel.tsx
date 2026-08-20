'use client';

import * as React from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { formatPrice, formatCurrency } from '@/lib/format';
import { toast } from 'sonner';
import { placeOrder } from '@/lib/api';
import type { Market, MarketOutcomeData } from '@/lib/types';
import { ShoppingCart, DollarSign, Network, Split, Loader2 } from 'lucide-react';

export function TradePanel({ market, className }: { market: Market; className?: string }) {
  const [side, setSide] = React.useState<'buy' | 'sell'>('buy');
  const [outcome, setOutcome] = React.useState<string>('YES');
  const [amount, setAmount] = React.useState('');
  const [shares, setShares] = React.useState('');
  const [isSubmitting, setIsSubmitting] = React.useState(false);

  const currentOutcome = market.outcomes.find((o) => o.label === outcome)!;
  const price = currentOutcome.price;
  const numShares = parseFloat(shares) || 0;
  const numAmount = parseFloat(amount) || 0;
  const totalCost = numShares * price;
  const potentialPayout = numShares * 100;
  const potentialProfit = potentialPayout - totalCost;

  const handleTrade = async () => {
    if (numShares <= 0 && numAmount <= 0) { toast.error('Enter an amount to trade'); return; }
    
    setIsSubmitting(true);
    try {
      await placeOrder(market.slug, {
        outcomeId: currentOutcome.id,
        side,
        orderType: 'market',
        timeInForce: 'GTC',
        shares: side === 'sell' ? numShares : (numShares > 0 ? numShares : undefined),
        amount: side === 'buy' && numAmount > 0 && numShares <= 0 ? numAmount : undefined,
      });
      toast.success(`${side === 'buy' ? 'Bought' : 'Sold'} ${outcome} successfully`);
      setAmount('');
      setShares('');
    } catch (err: any) {
      toast.error(err.message || 'Failed to place order');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className={cn('p-5', className)}>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="font-semibold">Trade</h3>
        <div className="flex rounded-lg border border-border p-0.5">
          <button onClick={() => setSide('buy')} className={cn('rounded-md px-3 py-1 text-sm font-medium transition-colors', side === 'buy' ? 'bg-success text-success-foreground' : 'text-muted-foreground')}>Buy</button>
          <button onClick={() => setSide('sell')} className={cn('rounded-md px-3 py-1 text-sm font-medium transition-colors', side === 'sell' ? 'bg-destructive text-destructive-foreground' : 'text-muted-foreground')}>Sell</button>
        </div>
      </div>
      <div className="mb-4 flex gap-2">
        {(['YES', 'NO'] as const).map((o) => (
          <button key={o} onClick={() => setOutcome(o)} className={cn('flex flex-1 items-center justify-between rounded-lg border p-3 transition-all', outcome === o ? (o === 'YES' ? 'border-success bg-success/10' : 'border-destructive bg-destructive/10') : 'border-border hover:border-foreground/20')}>
            <span className="font-semibold">{o}</span>
            <span className={cn('tabular-nums', o === 'YES' ? 'text-success' : 'text-destructive')}>{formatPrice(market.outcomes.find((x) => x.label === o)!.price)}</span>
          </button>
        ))}
      </div>
      <Tabs defaultValue="shares">
        <TabsList className="w-full">
          <TabsTrigger value="shares" className="flex-1"><ShoppingCart className="h-3.5 w-3.5 mr-1.5" />Shares</TabsTrigger>
          <TabsTrigger value="amount" className="flex-1"><DollarSign className="h-3.5 w-3.5 mr-1.5" />Amount</TabsTrigger>
        </TabsList>
        <TabsContent value="shares" className="space-y-3">
          <div><label className="mb-1.5 block text-xs font-medium text-muted-foreground">Shares</label><Input type="number" placeholder="0" value={shares} onChange={(e) => setShares(e.target.value)} /></div>
        </TabsContent>
        <TabsContent value="amount" className="space-y-3">
          <div><label className="mb-1.5 block text-xs font-medium text-muted-foreground">Amount (USD)</label><Input type="number" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} /></div>
          <div className="flex gap-2">{[10, 50, 100, 500].map((a) => <Button key={a} variant="outline" size="sm" className="flex-1" onClick={() => setAmount(String(a))}>${a}</Button>)}</div>
        </TabsContent>
      </Tabs>
      <div className="mt-4 space-y-2 rounded-lg bg-muted/50 p-3 text-sm">
        <div className="flex justify-between"><span className="text-muted-foreground">Price</span><span className="tabular-nums">{formatPrice(price)}</span></div>
        <div className="flex justify-between"><span className="text-muted-foreground">{side === 'buy' ? 'Total Cost' : 'Total Return'}</span><span className="tabular-nums font-medium">{formatCurrency(totalCost)}</span></div>
        {side === 'buy' && <div className="flex justify-between"><span className="text-muted-foreground">Potential Payout</span><span className="tabular-nums font-medium text-success">{formatCurrency(potentialPayout)}</span></div>}
        {side === 'buy' && potentialProfit > 0 && <div className="flex justify-between border-t border-border pt-2"><span className="text-muted-foreground">Potential Profit</span><span className="tabular-nums font-bold text-success">+{formatCurrency(potentialProfit)}</span></div>}
      </div>
      
      {/* Smart Order Routing Visualizer */}
      <div className="mt-4 rounded-lg border border-border p-3">
        <div className="mb-2 flex items-center justify-between">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-primary">
            <Network className="h-3.5 w-3.5" />
            Smart Order Routing
          </div>
          <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Best Price Guaranteed</span>
        </div>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs">
            <div className="flex w-16 shrink-0 items-center gap-1 font-medium"><Split className="h-3 w-3 text-muted-foreground" /> Split</div>
            <div className="flex h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
              <div className="bg-chart-1 h-full" style={{ width: '60%' }} />
              <div className="bg-chart-2 h-full" style={{ width: '40%' }} />
            </div>
          </div>
          <div className="flex justify-between text-xs text-muted-foreground">
            <div className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-chart-1" /> Polymarket (60%)</div>
            <div className="flex items-center gap-1.5"><div className="h-2 w-2 rounded-full bg-chart-2" /> Kalshi (40%)</div>
          </div>
        </div>
      </div>

      <Button className={cn('mt-4 w-full text-lg', side === 'buy' ? 'bg-success hover:bg-success/90' : 'bg-destructive hover:bg-destructive/90')} size="lg" onClick={handleTrade} disabled={isSubmitting}>
        {isSubmitting ? <Loader2 className="mr-2 h-5 w-5 animate-spin" /> : null}
        {side === 'buy' ? 'Buy' : 'Sell'} {outcome}
      </Button>
    </Card>
  );
}
