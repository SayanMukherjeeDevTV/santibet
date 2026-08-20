import { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { CategoryBadge } from '@/components/shared/category-badge';
import { StatusBadge } from '@/components/shared/status-badge';
import { formatCurrency, formatNumber, formatDate } from '@/lib/format';
import { adminMarkets } from '@/lib/mock-data';
import type { AdminMarket } from '@/lib/types';
import { MoreHorizontal, Flag, Edit, Trash2, Star, StarOff } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { fetchAdminMarkets, updateAdminMarket } from '@/lib/api';

export function AdminMarketsTable({ markets: initialMarkets, className }: { markets?: AdminMarket[]; className?: string }) {
  const [data, setData] = useState<AdminMarket[]>(initialMarkets || []);
  const [isLoading, setIsLoading] = useState(!initialMarkets);
  
  useEffect(() => {
    if (initialMarkets) {
      setData(initialMarkets);
      setIsLoading(false);
    } else {
      setIsLoading(true);
      fetchAdminMarkets()
        .then(res => setData(Array.isArray(res) ? res : res.items || []))
        .catch(console.error)
        .finally(() => setIsLoading(false));
    }
  }, [initialMarkets]);

  const handleToggleFeatured = async (market: AdminMarket) => {
    try {
      const newStatus = !market.featured;
      setData(prev => prev.map(m => m.id === market.id ? { ...m, featured: newStatus } : m));
      await updateAdminMarket(market.id, { featured: newStatus });
    } catch (e) {
      console.error('Failed to toggle featured status', e);
      setData(prev => prev.map(m => m.id === market.id ? { ...m, featured: market.featured } : m));
    }
  };

  return (
    <Card className={cn('p-0', className)}>
      <div className="flex items-center justify-between border-b p-4"><h3 className="font-semibold">Market Management</h3><Button size="sm">Create Market</Button></div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader><TableRow><TableHead>Question</TableHead><TableHead>Category</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Volume</TableHead><TableHead className="text-right">Traders</TableHead><TableHead>Created</TableHead><TableHead>Reports</TableHead><TableHead className="w-[50px]"></TableHead></TableRow></TableHeader>
          <TableBody>
            {data.map((m) => (
              <TableRow key={m.id}>
                <TableCell className="max-w-[300px] font-medium">
                  <div className="flex items-center gap-2">
                    {m.featured && <Star className="h-4 w-4 text-yellow-500 fill-yellow-500 shrink-0" />}
                    <span className="truncate" title={m.question}>{m.question}</span>
                  </div>
                </TableCell>
                <TableCell><CategoryBadge category={m.category} /></TableCell>
                <TableCell><StatusBadge status={m.status} /></TableCell>
                <TableCell className="text-right tabular-nums">{formatCurrency(m.volume, { compact: true })}</TableCell>
                <TableCell className="text-right tabular-nums">{formatNumber(m.traderCount, true)}</TableCell>
                <TableCell className="text-xs text-muted-foreground">{formatDate(m.createdAt)}</TableCell>
                <TableCell>{m.reported ? <Badge variant="destructive"><Flag className="h-3 w-3 mr-1" />Reported</Badge> : <span className="text-muted-foreground">\u2014</span>}</TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="h-8 w-8"><MoreHorizontal className="h-4 w-4" /></Button></DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => handleToggleFeatured(m)}>
                        {m.featured ? <StarOff className="h-3.5 w-3.5 mr-2" /> : <Star className="h-3.5 w-3.5 mr-2" />}
                        {m.featured ? 'Remove Featured' : 'Make Featured'}
                      </DropdownMenuItem>
                      <DropdownMenuItem><Edit className="h-3.5 w-3.5 mr-2" />Edit</DropdownMenuItem>
                      <DropdownMenuItem className="text-destructive"><Trash2 className="h-3.5 w-3.5 mr-2" />Delete</DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
