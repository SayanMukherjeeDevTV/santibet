'use client';

import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ChangeIndicator } from '@/components/shared/change-indicator';
import { formatCurrency, formatPrice, formatDate, formatDateTime } from '@/lib/format';
import { positions, transactions } from '@/lib/mock-data';
import type { Position, Transaction } from '@/lib/types';
import { ArrowDownLeft, ArrowUpRight, ShoppingCart, DollarSign, Percent } from 'lucide-react';

// ============================================================
// Status config for positions
// ============================================================
const positionStatusConfig: Record<Position['status'], { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  open: { label: 'Open', variant: 'secondary' },
  won: { label: 'Won', variant: 'default' },
  lost: { label: 'Lost', variant: 'destructive' },
  sold: { label: 'Sold', variant: 'outline' },
};

// ============================================================
// PositionsTable Component
// ============================================================
interface PositionsTableProps {
  positions?: Position[];
  compact?: boolean;
  className?: string;
}

export function PositionsTable({
  positions: data = positions,
  compact,
  className,
}: PositionsTableProps) {
  return (
    <Card className={cn('p-0', className)}>
      <div className="flex items-center justify-between border-b p-4">
        <h3 className="font-semibold">My Positions</h3>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/dashboard/positions">View All</Link>
        </Button>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Market</TableHead>
              <TableHead>Side</TableHead>
              <TableHead className="text-right">Shares</TableHead>
              <TableHead className="text-right">Avg Price</TableHead>
              <TableHead className="text-right">Current</TableHead>
              <TableHead className="text-right">Invested</TableHead>
              <TableHead className="text-right">Value</TableHead>
              <TableHead className="text-right">P&L</TableHead>
              {!compact && <TableHead>Status</TableHead>}
              {!compact && <TableHead>Opened</TableHead>}
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="max-w-[280px]">
                  <Link
                    href={`/markets/${p.marketSlug}`}
                    className="truncate text-sm font-medium hover:text-primary"
                  >
                    {p.question}
                  </Link>
                </TableCell>
                <TableCell>
                  <span
                    className={cn(
                      'font-medium',
                      p.outcome === 'YES' ? 'text-success' : 'text-destructive'
                    )}
                  >
                    {p.outcome}
                  </span>
                </TableCell>
                <TableCell className="text-right tabular-nums">{p.shares}</TableCell>
                <TableCell className="text-right tabular-nums">{formatPrice(p.avgPrice)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatPrice(p.currentPrice)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatCurrency(p.invested)}</TableCell>
                <TableCell className="text-right tabular-nums font-medium">
                  {formatCurrency(p.currentValue)}
                </TableCell>
                <TableCell className="text-right">
                  <ChangeIndicator value={p.pnlPercent} />
                </TableCell>
                {!compact && (
                  <TableCell>
                    <Badge variant={positionStatusConfig[p.status].variant}>
                      {positionStatusConfig[p.status].label}
                    </Badge>
                  </TableCell>
                )}
                {!compact && (
                  <TableCell className="text-xs text-muted-foreground">
                    {formatDate(p.openedAt)}
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}

// ============================================================
// Transaction type config (with icons)
// ============================================================
const typeConfig: Record<Transaction['type'], { icon: typeof ShoppingCart; color: string; sign: number }> = {
  deposit: { icon: ArrowDownLeft, color: 'text-success', sign: 1 },
  withdrawal: { icon: ArrowUpRight, color: 'text-destructive', sign: -1 },
  buy: { icon: ShoppingCart, color: 'text-foreground', sign: -1 },
  sell: { icon: ShoppingCart, color: 'text-foreground', sign: 1 },
  payout: { icon: DollarSign, color: 'text-success', sign: 1 },
  fee: { icon: Percent, color: 'text-muted-foreground', sign: -1 },
};

// ============================================================
// Transaction status config
// ============================================================
const transactionStatusConfig: Record<Transaction['status'], { label: string; variant: 'default' | 'secondary' | 'destructive' }> = {
  completed: { label: 'Completed', variant: 'default' },
  pending: { label: 'Pending', variant: 'secondary' },
  failed: { label: 'Failed', variant: 'destructive' },
};

// ============================================================
// TransactionsTable Component (with the cool icon design)
// ============================================================
interface TransactionsTableProps {
  transactions?: Transaction[];
  className?: string;
}

export function TransactionsTable({
  transactions: data = transactions,
  className,
}: TransactionsTableProps) {
  return (
    <Card className={cn('p-0', className)}>
      <div className="border-b p-4">
        <h3 className="font-semibold">Transaction History</h3>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Details</TableHead>
              <TableHead className="text-right">Amount</TableHead>
              <TableHead className="text-right">Balance After</TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">Date</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {data.map((t) => {
              const config = typeConfig[t.type];
              const Icon = config.icon;
              return (
                <TableRow key={t.id}>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          'flex h-7 w-7 items-center justify-center rounded-lg bg-muted',
                          config.color
                        )}
                      >
                        <Icon className="h-3.5 w-3.5" />
                      </span>
                      <span className="text-sm font-medium capitalize">{t.type}</span>
                    </div>
                  </TableCell>
                  <TableCell className="max-w-[200px] text-sm text-muted-foreground">
                    {t.question ?? '\u2014'}
                  </TableCell>
                  <TableCell
                    className={cn(
                      'text-right font-medium tabular-nums',
                      config.sign > 0 ? 'text-success' : 'text-destructive'
                    )}
                  >
                    {config.sign > 0 ? '+' : ''}
                    {formatCurrency(t.amount)}
                  </TableCell>
                  <TableCell className="text-right tabular-nums text-muted-foreground">
                    {formatCurrency(t.balanceAfter)}
                  </TableCell>
                  <TableCell>
                    <Badge variant={transactionStatusConfig[t.status].variant}>
                      {transactionStatusConfig[t.status].label}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-xs text-muted-foreground">
                    {formatDateTime(t.createdAt)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}