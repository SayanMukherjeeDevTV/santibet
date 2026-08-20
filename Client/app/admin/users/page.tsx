'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { AdminUsersTable } from '@/components/admin/admin-users-table';
import { StatCard } from '@/components/shared/stat-card';
import { fetchAdminUsers } from '@/lib/api';
import { formatCurrency } from '@/lib/format';
import { Users, Shield, TrendingUp, UserCheck } from 'lucide-react';
import { adminUsers as mockAdminUsers } from '@/lib/mock-data';

export default function AdminUsersPage() {
  const [users, setUsers] = React.useState<any[]>([]);

  React.useEffect(() => {
    fetchAdminUsers()
      .then(data => {
        if (Array.isArray(data)) {
          setUsers(data);
        } else if (data && Array.isArray(data.items)) {
          setUsers(data.items);
        } else {
          setUsers([]);
        }
      })
      .catch(console.error);
  }, []);

  const displayUsers = users.length > 0 ? users : mockAdminUsers;
  const totalBalance = displayUsers.reduce((s, u) => s + (u.balance || 0), 0);
  const totalVolume = displayUsers.reduce((s, u) => s + (u.volume || 0), 0);
  const activeCount = displayUsers.filter((u) => u.status === 'active' || u.accountStatus === 'active').length;

  return (
    <DashboardLayout variant="admin">
      <div className="space-y-6 p-6">
        <div><h1 className="font-display text-2xl font-bold">User Management</h1><p className="mt-1 text-sm text-muted-foreground">Manage user accounts, balances, and permissions</p></div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Total Users" value={String(displayUsers.length)} icon={Users} />
          <StatCard label="Active" value={String(activeCount)} icon={UserCheck} iconColor="text-success" />
          <StatCard label="Total Balance" value={formatCurrency(totalBalance, { compact: true })} icon={TrendingUp} iconColor="text-chart-2" />
          <StatCard label="Total Volume" value={formatCurrency(totalVolume, { compact: true })} icon={Shield} iconColor="text-chart-3" />
        </div>
        <AdminUsersTable users={users.length > 0 ? users : undefined} />
      </div>
    </DashboardLayout>
  );
}
