'use client';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { PositionsTable } from '@/components/dashboard/positions-table';
import { StatCard } from '@/components/shared/stat-card';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { formatCurrency, formatDate } from '@/lib/format';
import { Wallet, TrendingUp, Target, Percent } from 'lucide-react';
import * as React from 'react';
import { fetchUserOrders, cancelOrder, fetchUserPositions } from '@/lib/api';
import { toast } from 'sonner';

export default function PositionsPage() {
  const [positions, setPositions] = React.useState<any[]>([]);
  const openPositions = positions.filter((p) => p.status === 'open');
  const totalInvested = openPositions.reduce((sum, p) => sum + p.invested, 0);
  const totalValue = openPositions.reduce((sum, p) => sum + p.currentValue, 0);
  const totalPnl = totalValue - totalInvested;
  const pnlPercent = totalInvested > 0 ? (totalPnl / totalInvested) * 100 : 0;

  const [orders, setOrders] = React.useState<any[]>([]);
  const [loadingOrders, setLoadingOrders] = React.useState(true);

  const loadData = async () => {
    try {
      const [ordersData, positionsData] = await Promise.all([
        fetchUserOrders(),
        fetchUserPositions()
      ]);
      setOrders(ordersData || []);
      setPositions(positionsData || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingOrders(false);
    }
  };

  React.useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleCancelOrder = async (orderId: string) => {
    try {
      await cancelOrder(orderId);
      toast.success('Order cancelled successfully');
      loadData();
    } catch (err: any) {
      toast.error(err.message || 'Failed to cancel order');
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 p-6">
        <div><h1 className="font-display text-2xl font-bold">My Positions</h1><p className="mt-1 text-sm text-muted-foreground">Track and manage your open and closed positions</p></div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Total Invested" value={formatCurrency(totalInvested)} icon={Wallet} />
          <StatCard label="Current Value" value={formatCurrency(totalValue)} icon={TrendingUp} iconColor="text-chart-2" />
          <StatCard label="Unrealized P&L" value={formatCurrency(totalPnl)} icon={Target} iconColor={totalPnl >= 0 ? 'text-success' : 'text-destructive'} change={pnlPercent} />
          <StatCard label="Open Positions" value={String(openPositions.length)} icon={Percent} iconColor="text-chart-3" />
        </div>
        
        {/* Open Orders Section */}
        <Card className="p-5">
          <h3 className="mb-4 font-semibold">Active Orders</h3>
          {loadingOrders && orders.length === 0 ? (
            <div className="text-sm text-muted-foreground">Loading orders...</div>
          ) : orders.length === 0 ? (
            <div className="text-sm text-muted-foreground">No active orders</div>
          ) : (
            <div className="space-y-3">
              {orders.map((o) => (
                <div key={o.id} className="flex items-center justify-between rounded-lg border border-border p-4">
                  <div>
                    <p className="font-medium">{o.question}</p>
                    <p className="text-sm text-muted-foreground mt-1">
                      {o.side === 'buy' ? 'BUY' : 'SELL'} {o.outcomeLabel} • {o.sharesRequested} shares @ {o.limitPrice ? `${o.limitPrice * 100}¢` : 'Market'}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">Filled: {o.sharesFilled} / {o.sharesRequested} • {formatDate(o.createdAt)}</p>
                  </div>
                  <Button variant="destructive" size="sm" onClick={() => handleCancelOrder(o.id)}>Cancel</Button>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card className="p-5">
          <h3 className="mb-4 font-semibold">Position Summary</h3>
          {openPositions.length === 0 ? (
            <div className="text-sm text-muted-foreground">No open positions</div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {openPositions.map((p) => (
                <div key={p.id} className="rounded-lg border border-border p-4">
                  <div className="flex items-center justify-between"><span className={`text-sm font-medium ${p.outcome === 'YES' ? 'text-success' : 'text-destructive'}`}>{p.outcome}</span><span className="text-xs text-muted-foreground">{p.shares} shares</span></div>
                  <p className="mt-2 line-clamp-2 text-sm font-medium">{p.question}</p>
                  <div className="mt-3 flex items-center justify-between text-xs"><span className="text-muted-foreground">Avg: {p.avgPrice}¢</span><span className="text-muted-foreground">Now: {p.currentPrice}¢</span></div>
                  <div className="mt-2 flex items-center justify-between"><span className="text-sm font-medium">{formatCurrency(p.currentValue)}</span><span className={`text-sm font-bold ${p.pnl >= 0 ? 'text-success' : 'text-destructive'}`}>{p.pnl >= 0 ? '+' : ''}{formatCurrency(p.pnl)} ({p.pnlPercent.toFixed(1)}%)</span></div>
                </div>
              ))}
            </div>
          )}
        </Card>
        <PositionsTable positions={positions.length > 0 ? positions : undefined} />
      </div>
    </DashboardLayout>
  );
}
