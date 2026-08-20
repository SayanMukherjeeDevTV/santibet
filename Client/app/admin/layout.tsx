'use client';

import * as React from 'react';
import { useAuth } from '@/components/auth-context';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  React.useEffect(() => {
    if (!isLoading) {
      if (!user) {
        toast.error('You must be logged in to access this page.');
        router.replace('/login');
      } else if (user.role !== 'admin' && user.role !== 'superadmin') {
        toast.error('This page is for administrators only.');
        router.replace('/');
      }
    }
  }, [user, isLoading, router]);

  // While loading, or if not an admin, don't render the admin content.
  // The useEffect will handle the redirect.
  if (isLoading || !user || (user.role !== 'admin' && user.role !== 'superadmin')) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
      </div>
    );
  }

  return <>{children}</>;
}
