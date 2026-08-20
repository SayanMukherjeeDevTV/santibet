'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { fetchReports, updateReport } from '@/lib/api';
import { AlertTriangle, CheckCircle } from 'lucide-react';
import { toast } from 'sonner';
import { formatDate } from '@/lib/format';

export default function AdminReportsPage() {
  const [reports, setReports] = React.useState<any[]>([]);

  React.useEffect(() => {
    fetchReports()
      .then(data => setReports(data || []))
      .catch(console.error);
  }, []);

  const handleResolve = async (id: string) => {
    try {
      await updateReport(id, { status: 'resolved' });
      setReports((prev) => prev.filter(r => r.id !== id));
      toast.success('Report resolved');
    } catch (e) {
      toast.error('Failed to resolve report');
    }
  };

  const pendingReports = reports.filter(r => r.status !== 'resolved');

  return (
    <DashboardLayout variant="admin">
      <div className="space-y-6 p-6">
        <div>
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-6 w-6 text-destructive" />
            <h1 className="font-display text-2xl font-bold">User Reports</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">Manage and review reports submitted by users.</p>
        </div>

        <Card className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Target ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Date</TableHead>
                  <TableHead className="w-[100px]">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {pendingReports.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                      No pending reports.
                    </TableCell>
                  </TableRow>
                ) : (
                  pendingReports.map((report) => (
                    <TableRow key={report.id}>
                      <TableCell className="font-medium">{report.targetId}</TableCell>
                      <TableCell><Badge variant="outline">{report.type}</Badge></TableCell>
                      <TableCell className="max-w-[300px] truncate">{report.reason}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{formatDate(report.createdAt)}</TableCell>
                      <TableCell>
                        <Button onClick={() => handleResolve(report.id)} size="sm" variant="outline" className="text-success hover:text-success hover:bg-success/10">
                          <CheckCircle className="h-4 w-4 mr-1" /> Resolve
                        </Button>
                      </TableCell>
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
