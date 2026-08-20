'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { AdminMarketsTable } from '@/components/admin/admin-markets-table';
import { StatCard } from '@/components/shared/stat-card';
import { fetchAdminMarkets } from '@/lib/api';
import { formatCurrency } from '@/lib/format';
import { BarChart3, TrendingUp, Users, AlertTriangle } from 'lucide-react';
import { adminMarkets as mockAdminMarkets } from '@/lib/mock-data';

export default function AdminMarketsPage() {
  const [markets, setMarkets] = React.useState<any[]>([]);
  const [isMounted, setIsMounted] = React.useState(false);

  React.useEffect(() => {
    setIsMounted(true);
    fetchAdminMarkets()
      .then(data => {
        if (Array.isArray(data)) {
          setMarkets(data);
        } else if (data && Array.isArray(data.items)) {
          setMarkets(data.items);
        } else {
          setMarkets([]);
        }
      })
      .catch(console.error);
  }, []);

  if (!isMounted) return null;

  const totalVolume = markets.reduce((s, m) => s + (m.volume || m.totalVolume || 0), 0);
  const reportedCount = markets.filter(m => m.reported).length;

  return (
    <DashboardLayout variant="admin">
      <div className="space-y-6 p-6">
        <div><h1 className="font-display text-2xl font-bold">Market Management</h1><p className="mt-1 text-sm text-muted-foreground">Create, edit, and moderate prediction markets</p></div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Total Markets" value={String(markets.length)} icon={BarChart3} />
          <StatCard label="Total Volume" value={formatCurrency(totalVolume, { compact: true })} icon={TrendingUp} iconColor="text-success" />
          <StatCard label="Active Markets" value={String(markets.filter((m) => m.status === 'active').length)} icon={Users} iconColor="text-chart-2" />
          <StatCard label="Reported" value={String(reportedCount)} icon={AlertTriangle} iconColor="text-destructive" />
        </div>
        <AdminMarketsTable markets={markets} />
      </div>
    </DashboardLayout>
  );
}
