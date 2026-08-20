import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Activity } from 'lucide-react';

export function Logo({ className, showText = true, href = '/' }: { className?: string; showText?: boolean; href?: string }) {
  return (
    <Link href={href} className={cn('flex items-center gap-2 font-bold tracking-tight', className)}>
      <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-primary to-chart-2 text-primary-foreground shadow-sm">
        <Activity className="h-5 w-5" strokeWidth={2.5} />
      </div>
      {showText && <span className="font-display text-xl font-bold">Santi<span className="text-primary">Bet</span></span>}
    </Link>
  );
}
