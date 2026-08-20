'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/components/auth-context';
import { updateCurrentUser, fetchKycStatus, startKyc } from '@/lib/api';
import { currentUser as mockUser } from '@/lib/mock-data';
import { getInitials } from '@/lib/format';
import { toast } from 'sonner';

export default function ProfilePage() {
  const { user: authUser, setUser } = useAuth();
  const user = authUser || mockUser;
  const [name, setName] = React.useState(user.name);
  const [email, setEmail] = React.useState(user.email);
  const [saving, setSaving] = React.useState(false);
  const [kycStatus, setKycStatus] = React.useState('not_started');
  const [kycLoading, setKycLoading] = React.useState(false);

  React.useEffect(() => {
    if (authUser) {
      setName(authUser.name);
      setEmail(authUser.email);
    }
    fetchKycStatus().then(data => setKycStatus(data.status || 'not_started')).catch(console.error);
  }, [authUser]);

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateCurrentUser({ name });
      setUser(updated);
      toast.success('Profile updated successfully');
    } catch (e: any) {
      toast.error(e?.message || 'Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleStartKyc = async () => {
    setKycLoading(true);
    try {
      await startKyc();
      toast.success('Verification started!');
      const data = await fetchKycStatus();
      setKycStatus(data.status);
    } catch (e: any) {
      toast.error(e?.message || 'Failed to start verification');
    } finally {
      setKycLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6 p-6">
        <div>
          <h1 className="font-display text-2xl font-bold">User Profile</h1>
          <p className="mt-1 text-sm text-muted-foreground">Manage your personal information and preferences.</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="p-5">
            <h3 className="mb-4 font-semibold">Personal Information</h3>
            <div className="mb-6 flex items-center gap-4">
              <Avatar className="h-16 w-16 border-2 border-primary/20">
                <AvatarImage src={user.avatarUrl} />
                <AvatarFallback>{getInitials(user.name)}</AvatarFallback>
              </Avatar>
              <Button variant="outline" size="sm">Change Avatar</Button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Full Name</label>
                <Input value={name} onChange={(e) => setName(e.target.value)} />
              </div>
              <div>
                <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Email Address</label>
                <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>
              <Button onClick={handleSave} disabled={saving} className="w-full sm:w-auto">
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </Card>

          <div className="space-y-6">
            <Card className="p-5">
              <div className="mb-4 flex items-center justify-between">
                <h3 className="font-semibold">Identity Verification (KYC)</h3>
                <Badge variant={
                  kycStatus === 'approved' ? 'default' : 
                  kycStatus === 'rejected' ? 'destructive' : 
                  kycStatus === 'pending' ? 'secondary' : 'outline'
                }>
                  {kycStatus.replace('_', ' ').toUpperCase()}
                </Badge>
              </div>
              <p className="mb-4 text-sm text-muted-foreground">
                Verification is required for withdrawals and real-money trading.
              </p>
              {kycStatus === 'not_started' && (
                <Button onClick={handleStartKyc} disabled={kycLoading} className="w-full">
                  {kycLoading ? 'Starting...' : 'Start Verification'}
                </Button>
              )}
              {kycStatus === 'pending' && (
                <Button disabled className="w-full">Verification Pending</Button>
              )}
            </Card>

            <Card className="p-5">
              <h3 className="mb-4 font-semibold">Security Settings</h3>
              <div className="space-y-4">
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">Current Password</label>
                  <Input type="password" placeholder="••••••••" />
                </div>
                <div>
                  <label className="mb-1.5 block text-xs font-medium text-muted-foreground">New Password</label>
                  <Input type="password" placeholder="••••••••" />
                </div>
                <Button variant="secondary" onClick={() => toast.success('Password updated')}>Update Password</Button>
              </div>
            </Card>

            <Card className="p-5">
              <h3 className="mb-4 font-semibold">Danger Zone</h3>
              <p className="mb-4 text-sm text-muted-foreground">Permanently delete your account and all associated data.</p>
              <Button variant="destructive" onClick={() => toast.error('This action cannot be undone in this demo.')}>Delete Account</Button>
            </Card>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
