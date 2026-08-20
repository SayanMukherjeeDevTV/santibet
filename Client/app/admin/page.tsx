'use client';

import { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { StatCard } from '@/components/shared/stat-card';
import { Card } from '@/components/ui/card';
import { AreaChart, BarChart, DonutChart } from '@/components/charts/market-charts';
import { AdminMarketsTable } from '@/components/admin/admin-markets-table';
import { markets, tradingVolumeData, categories } from '@/lib/mock-data';
import { formatCurrency, formatNumber } from '@/lib/format';
import { Users, TrendingUp, BarChart3, DollarSign, Shield } from 'lucide-react';

const categoryDistribution = categories.map((c) => ({
  name: c.label,
  value: markets.filter((m) => m.category === c.id).length,
  color: `hsl(var(--chart-${(categories.indexOf(c) % 5) + 1}))`,
}));

const volumeData = [
  { t: 'Jan', volume: 4200000 }, { t: 'Feb', volume: 5800000 }, { t: 'Mar', volume: 7100000 },
  { t: 'Apr', volume: 6500000 }, { t: 'May', volume: 8900000 }, { t: 'Jun', volume: 9400000 },
];

export default function AdminPage() {
  const [platformStats, setPlatformStats] = useState<any>(null);

  useEffect(() => {
    fetch('/v1/platform-stats')
      .then((res) => res.json())
      .then((data) => setPlatformStats(data))
      .catch(console.error);
  }, []);

  return (
    <DashboardLayout variant="admin">
      <div className="space-y-6 p-6">
        <div className="flex items-center gap-2"><Shield className="h-6 w-6 text-primary" /><h1 className="font-display text-2xl font-bold">Admin Dashboard</h1></div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Total Volume" value={formatCurrency(platformStats?.totalVolume || 0, { compact: true })} icon={TrendingUp} change={12.4} />
          <StatCard label="Total Users" value={formatNumber(platformStats?.totalTraders || 0, true)} icon={Users} change={8.2} />
          <StatCard label="Active Markets" value={String(platformStats?.activeMarkets || 0)} icon={BarChart3} change={5.1} />
          <StatCard label="Total Markets" value={String(platformStats?.totalMarkets || 0)} icon={DollarSign} change={15.7} />
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <Card className="p-5 lg:col-span-2">
            <div className="mb-4"><h3 className="font-semibold">Platform Volume</h3><p className="text-sm text-muted-foreground">Monthly trading volume</p></div>
            <BarChart data={volumeData} xKey="t" bars={[{ key: 'volume', color: 'hsl(166 72% 45%)' }]} height={280} yFormatter={(v) => formatCurrency(v, { compact: true })} />
          </Card>
          <Card className="p-5">
            <h3 className="mb-4 font-semibold">Markets by Category</h3>
            <DonutChart data={categoryDistribution} height={200} />
            <div className="mt-4 space-y-1.5">
              {categoryDistribution.map((d) => (
                <div key={d.name} className="flex items-center justify-between text-sm">
                  <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: d.color }} />{d.name}</span>
                  <span className="font-medium">{d.value}</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
        <AdminMarketsTable />
      </div>
    </DashboardLayout>
  );
}
