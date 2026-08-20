'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { LayoutDashboard, Wallet, ListOrdered, Brain, Shield, ArrowLeft, Settings, User, ListChecks } from 'lucide-react';
import { Button } from '@/components/ui/button';

const dashboardLinks = [
  { href: '/dashboard', label: 'Overview', icon: LayoutDashboard },
  { href: '/dashboard/wallet', label: 'Wallet', icon: Wallet },
  { href: '/dashboard/positions', label: 'Positions', icon: ListOrdered },
  { href: '/dashboard/ai-picks', label: 'AI Picks', icon: Brain },
  { href: '/dashboard/profile', label: 'Profile', icon: User },
];

const adminLinks = [
  { href: '/admin', label: 'Overview', icon: LayoutDashboard },
  { href: '/admin/markets', label: 'Markets', icon: Shield },
  { href: '/admin/users', label: 'Users', icon: Settings },
  { href: '/admin/ai-review', label: 'AI Review', icon: ListChecks },
  { href: '/admin/reports', label: 'Reports', icon: Shield }, // we can use FileText but lucide-react might not have it imported
  { href: '/admin/audit-log', label: 'Audit Log', icon: ListOrdered },
];

export function Sidebar({ variant }: { variant: 'dashboard' | 'admin' }) {
  const pathname = usePathname();
  const links = variant === 'admin' ? adminLinks : dashboardLinks;
  return (
    <aside className="sticky top-0 hidden h-screen w-60 shrink-0 flex-col border-r border-border bg-card/30 lg:flex">
      <div className="flex flex-1 flex-col gap-1 overflow-y-auto p-4 scrollbar-thin">
        <div className="mb-2 px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{variant === 'admin' ? 'Admin Panel' : 'My Account'}</div>
        {links.map((link) => {
          const active = pathname === link.href;
          return <Link key={link.href} href={link.href} className={cn('flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors', active ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground')}><link.icon className="h-4 w-4" />{link.label}</Link>;
        })}
        <div className="mt-auto pt-4"><Button variant="ghost" size="sm" asChild className="w-full justify-start text-muted-foreground"><Link href="/"><ArrowLeft className="h-4 w-4" />Back to Site</Link></Button></div>
      </div>
    </aside>
  );
}

export function MobileSidebar({ variant }: { variant: 'dashboard' | 'admin' }) {
  const pathname = usePathname();
  const links = variant === 'admin' ? adminLinks : dashboardLinks;
  return (
    <div className="flex items-center gap-1 overflow-x-auto border-b border-border bg-card/30 px-4 py-2 scrollbar-hide lg:hidden">
      {links.map((link) => {
        const active = pathname === link.href;
        return <Link key={link.href} href={link.href} className={cn('flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition-colors', active ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted')}><link.icon className="h-3.5 w-3.5" />{link.label}</Link>;
      })}
    </div>
  );
}
