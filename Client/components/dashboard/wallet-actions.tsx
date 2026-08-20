'use client';

import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { formatCurrency } from '@/lib/format';
import { ArrowDownToLine, ArrowUpFromLine, Wallet } from 'lucide-react';

export function WalletActions({ balance, className }: { balance: number; className?: string }) {
  return (
    <Card className={cn("p-5 flex flex-col justify-between", className)}>
      <div>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="text-sm text-muted-foreground">Available Balance</p>
            <p className="font-display text-2xl font-bold">{formatCurrency(balance)}</p>
          </div>
          <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10">
            <Wallet className="h-6 w-6 text-primary" />
          </div>
        </div>
        <p className="text-sm text-muted-foreground mb-6">
          Use the buttons below to manage your funds. Deposits are processed instantly for crypto, and within 1-2 days for bank transfers.
        </p>
      </div>
      <div className="flex gap-3">
        <Button className="flex-1" asChild>
          <Link href="/dashboard/wallet/deposit">
            <ArrowDownToLine className="h-4 w-4 mr-2" /> Deposit
          </Link>
        </Button>
        <Button variant="secondary" className="flex-1" asChild>
          <Link href="/dashboard/wallet/withdraw">
            <ArrowUpFromLine className="h-4 w-4 mr-2" /> Withdraw
          </Link>
        </Button>
      </div>
    </Card>
  );
}
