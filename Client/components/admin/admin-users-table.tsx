import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { formatCurrency, formatDate, getInitials } from '@/lib/format';
import { adminUsers } from '@/lib/mock-data';
import type { AdminUser } from '@/lib/types';
import { MoreHorizontal, Ban, CheckCircle, Edit, Shield } from 'lucide-react';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';

const statusConfig: Record<AdminUser['status'], { label: string; variant: 'default' | 'secondary' | 'destructive' }> = {
  active: { label: 'Active', variant: 'default' }, suspended: { label: 'Suspended', variant: 'secondary' }, banned: { label: 'Banned', variant: 'destructive' },
};

export function AdminUsersTable({ users: data = adminUsers, className }: { users?: AdminUser[]; className?: string }) {
  return (
    <Card className={cn('p-0', className)}>
      <div className="flex items-center justify-between border-b p-4"><h3 className="font-semibold">User Management</h3><Button size="sm">Add User</Button></div>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader><TableRow><TableHead>User</TableHead><TableHead>Balance</TableHead><TableHead className="text-right">Volume</TableHead><TableHead>Status</TableHead><TableHead>Joined</TableHead><TableHead>Verified</TableHead><TableHead className="w-[50px]"></TableHead></TableRow></TableHeader>
          <TableBody>
            {data.map((u) => (
              <TableRow key={u.id}>
                <TableCell><div className="flex items-center gap-3"><Avatar className="h-8 w-8"><AvatarImage src={`https://api.dicebear.com/7.x/initials/svg?seed=${u.name}`} /><AvatarFallback>{getInitials(u.name)}</AvatarFallback></Avatar><div><div className="text-sm font-medium">{u.name}</div><div className="text-xs text-muted-foreground">{u.email}</div></div></div></TableCell>
                <TableCell className="tabular-nums">{formatCurrency(u.balance, { compact: true })}</TableCell>
                <TableCell className="text-right tabular-nums">{formatCurrency(u.volume, { compact: true })}</TableCell>
                <TableCell><Badge variant={statusConfig[u.status].variant}>{statusConfig[u.status].label}</Badge></TableCell>
                <TableCell className="text-xs text-muted-foreground">{formatDate(u.joinedAt)}</TableCell>
                <TableCell>{u.verified ? <CheckCircle className="h-4 w-4 text-success" /> : <span className="text-muted-foreground">\u2014</span>}</TableCell>
                <TableCell>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild><Button variant="ghost" size="icon" className="h-8 w-8"><MoreHorizontal className="h-4 w-4" /></Button></DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem><Edit className="h-3.5 w-3.5 mr-2" />Edit User</DropdownMenuItem>
                      <DropdownMenuItem><Shield className="h-3.5 w-3.5 mr-2" />Change Role</DropdownMenuItem>
                      <DropdownMenuItem className="text-destructive"><Ban className="h-3.5 w-3.5 mr-2" />Ban User</DropdownMenuItem>
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
