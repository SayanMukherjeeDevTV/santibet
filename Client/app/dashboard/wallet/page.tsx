'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { WalletActions } from '@/components/dashboard/wallet-actions';
import { TransactionsTable } from '@/components/dashboard/transactions-table';
import { StatCard } from '@/components/shared/stat-card';
import { Card } from '@/components/ui/card';
import { AreaChart } from '@/components/charts/market-charts';
import { currentUser } from '@/lib/mock-data';
import { formatCurrency } from '@/lib/format';
import { Wallet, TrendingUp, ArrowDownToLine, ArrowUpFromLine } from 'lucide-react';
import { fetchWalletBalance, fetchWalletTransactions } from '@/lib/api';
import type { Transaction } from '@/lib/types';
import { Button } from '@/components/ui/button';

export default function WalletPage() {
  const user = currentUser;
  const [balance, setBalance] = React.useState(0);
  const [totalDeposited, setTotalDeposited] = React.useState(0);
  const [totalWithdrawn, setTotalWithdrawn] = React.useState(0);
  const [transactions, setTransactions] = React.useState<Transaction[]>([]);

  React.useEffect(() => {
    fetchWalletBalance().then(data => setBalance(data.balance || 0)).catch(console.error);
    fetchWalletTransactions().then(data => {
      if (Array.isArray(data)) {
        setTransactions(data);
        const deposits = data.filter(t => t.type === 'deposit').reduce((sum, t) => sum + t.amount, 0);
        const withdrawals = data.filter(t => t.type === 'withdrawal').reduce((sum, t) => sum + t.amount, 0);
        setTotalDeposited(deposits);
        setTotalWithdrawn(withdrawals);
      }
    }).catch(console.error);
  }, []);

  const balanceData = [
    { t: 'Jan', v: 8000 }, { t: 'Feb', v: 10000 }, { t: 'Mar', v: 9500 },
    { t: 'Apr', v: 12000 }, { t: 'May', v: 11500 }, { t: 'Jun', v: balance },
  ];

  return (
    <DashboardLayout>
      <div className="space-y-6 p-6">
        <div><h1 className="font-display text-2xl font-bold">Wallet</h1><p className="mt-1 text-sm text-muted-foreground">Manage your funds, deposits, and withdrawals</p></div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Total Balance" value={formatCurrency(balance)} icon={Wallet} />
          <StatCard label="Portfolio Value" value={formatCurrency(user.portfolioValue)} icon={TrendingUp} iconColor="text-chart-2" change={user.totalPnlPercent} />
          <StatCard label="Total Deposited" value={formatCurrency(totalDeposited)} icon={ArrowDownToLine} iconColor="text-success" />
          <StatCard label="Total Withdrawn" value={formatCurrency(totalWithdrawn)} icon={ArrowUpFromLine} iconColor="text-destructive" />
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-4">
            <WalletActions balance={balance} />
            <Card className="p-4 flex justify-between items-center bg-muted/30">
              <span className="text-sm font-medium">Debug Tools</span>
              <Button size="sm" variant="outline" onClick={() => {
                import('@/lib/api').then(api => {
                  api.testStripeWebhook({ type: 'payment_intent.succeeded', data: { object: { id: 'test_123' } } })
                     .then(() => alert('Webhook fired!'))
                     .catch(e => alert('Webhook rejected (expected): ' + e.message));
                })
              }}>
                Test Stripe Webhook
              </Button>
            </Card>
          </div>
          <Card className="p-5 lg:col-span-2">
            <div className="mb-4"><h3 className="font-semibold">Balance History</h3><p className="text-sm text-muted-foreground">Available balance over the last 6 months</p></div>
            <AreaChart data={balanceData} xKey="t" areas={[{ key: 'v', color: 'hsl(166 72% 45%)', name: 'Balance' }]} height={280} yFormatter={(v) => formatCurrency(v, { compact: true })} />
          </Card>
        </div>
        <TransactionsTable transactions={transactions.length > 0 ? transactions : undefined} />
      </div>
    </DashboardLayout>
  );
}
