'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { StatCard } from '@/components/shared/stat-card';
import { PositionsTable } from '@/components/dashboard/positions-table';
import { ChangeIndicator } from '@/components/shared/change-indicator';
import { AreaChart, DonutChart } from '@/components/charts/market-charts';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { currentUser, portfolioChartData, pnlBreakdownData, tradingVolumeData } from '@/lib/mock-data';
import { formatCurrency, formatNumber, getInitials, formatDate } from '@/lib/format';
import { Wallet, TrendingUp, Target, Award, BarChart3 } from 'lucide-react';
import { fetchUserPositions } from '@/lib/api';
import { useAuth } from '@/components/auth-context';

export default function DashboardPage() {
  const { user: authUser } = useAuth();
  const user = authUser ? { ...currentUser, ...authUser } : currentUser;
  const [positions, setPositions] = React.useState<any[]>([]);

  React.useEffect(() => {
    fetchUserPositions()
      .then(data => setPositions(data || []))
      .catch(console.error);
  }, []);

  return (
    <DashboardLayout>
      <div className="space-y-6 p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-4">
            <Avatar className="h-14 w-14 border-2 border-primary/20">
              <AvatarFallback className="bg-primary text-primary-foreground text-xl">
                {getInitials(user.name || 'User')}
              </AvatarFallback>
            </Avatar>
            <div>
              <h1 className="font-display text-2xl font-bold">{user.name}</h1>
              <p className="text-sm text-muted-foreground">Rank #{user.rank || '-'} · Joined {user.joinedAt ? formatDate(user.joinedAt) : 'Unknown'}</p>
            </div>
          </div>
          <ChangeIndicator value={user.totalPnlPercent} className="text-lg" />
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Portfolio Value" value={formatCurrency(user.portfolioValue)} icon={Wallet} change={user.totalPnlPercent} />
          <StatCard label="Available Balance" value={formatCurrency(user.balance)} icon={TrendingUp} iconColor="text-chart-2" />
          <StatCard label="Total P&L" value={formatCurrency(user.totalPnl)} icon={Target} iconColor="text-success" change={user.totalPnlPercent} />
          <StatCard label="Global Rank" value={`#${user.rank}`} icon={Award} iconColor="text-chart-3" />
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="p-5 lg:col-span-2">
            <div className="mb-4 flex items-center justify-between"><div><h3 className="font-semibold">Portfolio Value Over Time</h3><p className="text-sm text-muted-foreground">Last 4 months</p></div></div>
            <AreaChart data={portfolioChartData} xKey="t" areas={[{ key: 'value', color: 'hsl(166 72% 45%)', name: 'Portfolio' }]} height={280} yFormatter={(v) => formatCurrency(v, { compact: true })} />
          </Card>
          <Card className="p-5">
            <h3 className="mb-4 font-semibold">P&L Breakdown by Category</h3>
            <DonutChart data={pnlBreakdownData} height={200} formatter={(v) => formatCurrency(v)} />
            <div className="mt-4 space-y-1.5">
              {pnlBreakdownData.map((d) => (
                <div key={d.name} className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: d.color }} />{d.name}</span>
                  <span className={d.value >= 0 ? 'text-success' : 'text-destructive'}>{formatCurrency(d.value)}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>

        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="p-5 lg:col-span-2"><h3 className="mb-4 font-semibold">Trading Volume (7 days)</h3><AreaChart data={tradingVolumeData} xKey="t" areas={[{ key: 'volume', color: 'hsl(200 85% 55%)', name: 'Volume' }]} height={200} yFormatter={(v) => formatCurrency(v, { compact: true })} /></Card>
          <Card className="p-5">
            <div className="mb-3 flex items-center gap-2"><BarChart3 className="h-5 w-5 text-primary" /><h3 className="font-semibold">Quick Stats</h3></div>
            <div className="space-y-3">
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">Open Positions</span><span className="font-medium">5</span></div>
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">Won Positions</span><span className="font-medium text-success">1</span></div>
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">Win Rate</span><span className="font-medium">83.3%</span></div>
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">Markets Traded</span><span className="font-medium">28</span></div>
              <div className="flex justify-between text-sm"><span className="text-muted-foreground">Avg. Position Size</span><span className="font-medium">{formatCurrency(446)}</span></div>
            </div>
          </Card>
        </div>

        <PositionsTable compact positions={positions.length > 0 ? positions : undefined} />
      </div>
    </DashboardLayout>
  );
}
