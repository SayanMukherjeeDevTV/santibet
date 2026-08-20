import { Sidebar, MobileSidebar } from '@/components/layout/sidebar';

export function DashboardLayout({ children, variant = 'dashboard' }: { children: React.ReactNode; variant?: 'dashboard' | 'admin' }) {
  return (
    <div className="flex min-h-screen flex-col">
      <MobileSidebar variant={variant} />
      <div className="flex flex-1">
        <Sidebar variant={variant} />
        <div className="flex-1 overflow-x-hidden">{children}</div>
      </div>
    </div>
  );
}
