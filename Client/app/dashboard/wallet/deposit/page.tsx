'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { formatCurrency } from '@/lib/format';
import { toast } from 'sonner';
import { CreditCard, Bitcoin, Wallet as WalletIcon, ArrowDownToLine, ArrowLeft } from 'lucide-react';
import Link from 'next/link';
import { depositFunds } from '@/lib/api';

const paymentMethods = [
  { id: 'card', label: 'Credit Card', icon: CreditCard, details: 'Visa, Mastercard, Amex' },
  { id: 'crypto', label: 'Cryptocurrency', icon: Bitcoin, details: 'BTC, ETH, USDC' },
  { id: 'bank', label: 'Bank Transfer', icon: WalletIcon, details: 'ACH, Wire Transfer' },
];

export default function DepositPage() {
  const [amount, setAmount] = React.useState('');
  const [method, setMethod] = React.useState('card');

  const [loading, setLoading] = React.useState(false);

  const handleDeposit = async () => {
    if (!amount || parseFloat(amount) <= 0) { 
      toast.error('Enter a valid amount'); 
      return; 
    }
    setLoading(true);
    try {
      await depositFunds(parseFloat(amount), method);
      toast.success(`Deposit of ${formatCurrency(parseFloat(amount))} initiated via ${method}`);
      setAmount('');
    } catch (err: any) {
      toast.error(err.message || 'Failed to deposit funds');
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
            <ArrowDownToLine className="h-6 w-6 text-primary" />
            <h1 className="font-display text-2xl font-bold">Deposit Funds</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">Add funds to your SantiBet account to start trading.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="p-5">
            <h3 className="mb-4 font-semibold">Select Payment Method</h3>
            <div className="space-y-3">
              {paymentMethods.map((m) => (
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
          </Card>

          <Card className="p-5">
            <h3 className="mb-4 font-semibold">Deposit Details</h3>
            <div className="space-y-6">
              <div>
                <label className="mb-1.5 block text-sm font-medium text-muted-foreground">Amount (USD)</label>
                <Input type="number" placeholder="0.00" value={amount} onChange={(e) => setAmount(e.target.value)} className="text-lg" />
              </div>
              <div className="flex gap-2">
                {[50, 100, 500, 1000].map((a) => (
                  <Button key={a} variant="outline" size="sm" className="flex-1" onClick={() => setAmount(String(a))}>
                    ${a}
                  </Button>
                ))}
              </div>
              <div className="rounded-lg bg-muted/50 p-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Deposit Amount</span>
                  <span>{formatCurrency(parseFloat(amount) || 0)}</span>
                </div>
                <div className="mt-2 flex justify-between text-sm">
                  <span className="text-muted-foreground">Processing Fee</span>
                  <span>Free</span>
                </div>
                <div className="my-3 h-px bg-border" />
                <div className="flex justify-between font-semibold">
                  <span>Total Credited</span>
                  <span className="text-primary">{formatCurrency(parseFloat(amount) || 0)}</span>
                </div>
              </div>
              <Button className="w-full" size="lg" onClick={handleDeposit}>
                Complete Deposit
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
