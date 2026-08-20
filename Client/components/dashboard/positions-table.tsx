import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ChangeIndicator } from '@/components/shared/change-indicator';
import { formatCurrency, formatPrice, formatDate } from '@/lib/format';
import { positions } from '@/lib/mock-data';
import type { Position } from '@/lib/types';

const statusConfig: Record<Position['status'], { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' }> = {
  open: { label: 'Open', variant: 'secondary' }, won: { label: 'Won', variant: 'default' },
  lost: { label: 'Lost', variant: 'destructive' }, sold: { label: 'Sold', variant: 'outline' },
};

export function PositionsTable({ positions: data = positions, compact, className }: { positions?: Position[]; compact?: boolean; className?: string }) {
  return (
    <Card className={cn('p-0', className)}>
      <div className="flex items-center justify-between border-b p-4">
        <h3 className="font-semibold">My Positions</h3>
        <Button variant="ghost" size="sm" asChild><Link href="/dashboard/positions">View All</Link></Button>
      </div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader><TableRow>
            <TableHead>Market</TableHead><TableHead>Side</TableHead><TableHead className="text-right">Shares</TableHead>
            <TableHead className="text-right">Avg Price</TableHead><TableHead className="text-right">Current</TableHead>
            <TableHead className="text-right">Invested</TableHead><TableHead className="text-right">Value</TableHead>
            <TableHead className="text-right">P&L</TableHead>
            {!compact && <TableHead>Status</TableHead>}{!compact && <TableHead>Opened</TableHead>}
          </TableRow></TableHeader>
          <TableBody>
            {data.map((p) => (
              <TableRow key={p.id}>
                <TableCell className="max-w-[280px]"><Link href={`/markets/${p.marketSlug}`} className="truncate text-sm font-medium hover:text-primary">{p.question}</Link></TableCell>
                <TableCell><span className={cn('font-medium', p.outcome === 'YES' ? 'text-success' : 'text-destructive')}>{p.outcome}</span></TableCell>
                <TableCell className="text-right tabular-nums">{p.shares}</TableCell>
                <TableCell className="text-right tabular-nums">{formatPrice(p.avgPrice)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatPrice(p.currentPrice)}</TableCell>
                <TableCell className="text-right tabular-nums">{formatCurrency(p.invested)}</TableCell>
                <TableCell className="text-right tabular-nums font-medium">{formatCurrency(p.currentValue)}</TableCell>
                <TableCell className="text-right"><ChangeIndicator value={p.pnlPercent} /></TableCell>
                {!compact && <TableCell><Badge variant={statusConfig[p.status].variant}>{statusConfig[p.status].label}</Badge></TableCell>}
                {!compact && <TableCell className="text-xs text-muted-foreground">{formatDate(p.openedAt)}</TableCell>}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
