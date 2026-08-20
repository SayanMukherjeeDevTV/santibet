'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { fetchAuditLog } from '@/lib/api';
import { ListOrdered } from 'lucide-react';
import { formatDate } from '@/lib/format';
import { AuditLogEntry } from '@/lib/types';

export default function AdminAuditLogPage() {
  const [logs, setLogs] = React.useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetchAuditLog()
      .then((data) => {
        if (Array.isArray(data)) {
          setLogs(data);
        } else if (data && Array.isArray(data.items)) {
          setLogs(data.items);
        } else {
          setLogs([]);
        }
      })
      .catch((err) => {
        console.error('Failed to fetch audit log:', err);
        setLogs([]);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  const formatDetails = (log: AuditLogEntry) => {
    const details = log.details || log.after || log.before;
    if (!details) {
      if (log.targetType || log.targetId) {
        return `${log.targetType || 'Target'}: ${log.targetId || '-'}`;
      }
      return '-';
    }
    if (typeof details === 'string') return details;
    return JSON.stringify(details);
  };

  return (
    <DashboardLayout variant="admin">
      <div className="space-y-6 p-6">
        <div>
          <div className="flex items-center gap-2">
            <ListOrdered className="h-6 w-6 text-primary" />
            <h1 className="font-display text-2xl font-bold">System Audit Log</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">Track all administrative actions across the platform.</p>
        </div>

        <Card className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Date</TableHead>
                  <TableHead>Actor / Admin</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead>Target</TableHead>
                  <TableHead>Details</TableHead>
                  <TableHead>IP Address</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {loading ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                      Loading audit logs...
                    </TableCell>
                  </TableRow>
                ) : logs.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="h-24 text-center text-muted-foreground">
                      No audit logs found.
                    </TableCell>
                  </TableRow>
                ) : (
                  logs.map((log) => (
                    <TableRow key={log.id}>
                      <TableCell className="text-xs text-muted-foreground whitespace-nowrap">{formatDate(log.createdAt)}</TableCell>
                      <TableCell className="font-medium text-xs font-mono">{log.actorUserId || log.adminId || 'System'}</TableCell>
                      <TableCell>
                        <Badge variant="outline" className="bg-primary/5 text-primary border-primary/20">{log.action}</Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground">
                        {log.targetType ? (
                          <span className="inline-flex items-center gap-1">
                            <span className="font-semibold capitalize">{log.targetType}</span>
                            {log.targetId && <span className="font-mono text-[11px]">({log.targetId.slice(0, 8)}...)</span>}
                          </span>
                        ) : (
                          log.targetId || '-'
                        )}
                      </TableCell>
                      <TableCell className="max-w-[320px] truncate text-xs font-mono text-muted-foreground" title={formatDetails(log)}>
                        {formatDetails(log)}
                      </TableCell>
                      <TableCell className="text-xs font-mono text-muted-foreground">{log.ip || log.ipAddress || '-'}</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </Card>
      </div>
    </DashboardLayout>
  );
}

