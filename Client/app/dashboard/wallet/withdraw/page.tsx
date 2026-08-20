'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { formatCurrency } from '@/lib/format';
import { currentUser } from '@/lib/mock-data';
import { toast } from 'sonner';
import { CreditCard, Bitcoin, Wallet as WalletIcon, ArrowUpFromLine, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { withdrawFunds, fetchWalletBalance } from '@/lib/api';

const withdrawalMethods = [
  { id: 'bank', label: 'Bank Transfer', icon: WalletIcon, details: '2-3 business days' },
  { id: 'crypto', label: 'Cryptocurrency', icon: Bitcoin, details: 'Instant (USDC, BTC, ETH)' },
  { id: 'card', label: 'Debit Card', icon: CreditCard, details: '1-2 business days' },
];

export default function WithdrawPage() {
  const [balance, setBalance] = React.useState(0);
  const [amount, setAmount] = React.useState('');
  const [method, setMethod] = React.useState('bank');
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    fetchWalletBalance().then(data => setBalance(data.balance || 0)).catch(console.error);
  }, []);

  const handleWithdraw = async () => {
    if (!amount || parseFloat(amount) <= 0) { 
      toast.error('Enter a valid amount'); 
      return; 
    }
    if (parseFloat(amount) > balance) {
      toast.error('Insufficient funds');
      return;
    }
    setLoading(true);
    try {
      await withdrawFunds(parseFloat(amount), method);
      toast.success(`Withdrawal of ${formatCurrency(parseFloat(amount))} initiated via ${method}`);
      setAmount('');
      // Refresh balance after successful withdrawal
      const data = await fetchWalletBalance();
      setBalance(data.balance || 0);
    } catch (err: any) {
      toast.error(err.message || 'Failed to request withdrawal');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 p-6">
        <div>
          <Link href="/dashboard/wallet" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Back to Wallet
          </Link>
          <div className="flex items-center gap-2">
            <ArrowUpFromLine className="h-6 w-6 text-primary" />
            <h1 className="font-display text-2xl font-bold">Withdraw Funds</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">Transfer funds from your SantiBet account to your personal accounts.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="p-5">
            <h3 className="mb-4 font-semibold">Select Withdrawal Method</h3>
            <div className="space-y-3">
              {withdrawalMethods.map((m) => (
                <button 
                  key={m.id} 
                  onClick={() => setMethod(m.id)}
                  className={`flex w-full items-center gap-3 rounded-xl border p-4 text-left transition-all ${method === m.id ? 'border-primary bg-primary/5 ring-1 ring-primary' : 'border-border hover:border-foreground/20'}`}
                >
                  <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg ${method === m.id ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                    <m.icon className="h-5 w-5" />
                  </div>
                  <div>
                    <p className="font-medium">{m.label}</p>
                    <p className="text-xs text-muted-foreground">{m.details}</p>
                  </div>
                </button>
              ))}
            </div>
            
            <div className="mt-6 space-y-4">
              <h3 className="font-semibold">Destination Details</h3>
              {method === 'bank' && (
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Bank Account / IBAN</label>
                  <Input placeholder="Enter account details..." />
                </div>
              )}
              {method === 'crypto' && (
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Wallet Address (ERC-20)</label>
                  <Input placeholder="0x..." />
                </div>
              )}
              {method === 'card' && (
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Linked Debit Card</label>
                  <Input placeholder="**** **** **** 1234" disabled />
                </div>
              )}
            </div>
          </Card>

          <Card className="p-5">
            <h3 className="mb-4 font-semibold">Withdrawal Details</h3>
            <div className="space-y-6">
              <div>
                <div className="mb-1.5 flex justify-between">
                  <label className="block text-sm font-medium text-muted-foreground">Amount (USD)</label>
                  <span className="text-xs text-muted-foreground">Available: {formatCurrency(balance)}</span>
                </div>
                <Input type="number" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} className="text-lg" />
              </div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" className="flex-1" onClick={() => setAmount(String(balance * 0.25))}>25%</Button>
                <Button variant="outline" size="sm" className="flex-1" onClick={() => setAmount(String(balance * 0.5))}>50%</Button>
                <Button variant="outline" size="sm" className="flex-1" onClick={() => setAmount(String(balance * 0.75))}>75%</Button>
                <Button variant="outline" size="sm" className="flex-1" onClick={() => setAmount(String(balance))}>Max</Button>
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Withdrawal Amount</span>
                  <span>{formatCurrency(parseFloat(amount) || 0)}</span>
                </div>
                <div className="mt-2 flex justify-between text-sm">
                  <span className="text-muted-foreground">Network / Processing Fee</span>
                  <span>{formatCurrency((parseFloat(amount) || 0) > 0 ? 2.50 : 0)}</span>
                </div>
                <div className="my-3 h-px bg-border" />
                <div className="flex justify-between font-semibold">
                  <span>Total Received</span>
                  <span className="text-primary">{formatCurrency(Math.max(0, (parseFloat(amount) || 0) - 2.50))}</span>
                </div>
              </div>
              <Button className="w-full" size="lg" onClick={handleWithdraw}>
                Request Withdrawal
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
