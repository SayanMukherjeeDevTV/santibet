'use client';

import * as React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import { Logo } from '@/components/shared/logo';
import { ThemeToggle } from '@/components/shared/theme-toggle';
import { Button } from '@/components/ui/button';
import { Sheet, SheetContent, SheetTrigger, SheetTitle } from '@/components/ui/sheet';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger } from '@/components/ui/dropdown-menu';
import { BarChart3, Brain, LayoutDashboard, ListOrdered, Menu, Search, Trophy, Wallet, Settings, LogOut } from 'lucide-react';
import { useAuth } from '@/components/auth-context';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';
import { getInitials } from '@/lib/format';

const navLinks = [
  { href: '/markets', label: 'Markets', icon: BarChart3 },
  { href: '/ai-recommendations', label: 'AI Picks', icon: Brain },
];

const userLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/dashboard/wallet', label: 'Wallet', icon: Wallet },
  { href: '/dashboard/positions', label: 'Positions', icon: ListOrdered },
];

export function Navbar() {
  const pathname = usePathname();
  const router = useRouter();
  const { user, setUser, isLoading } = useAuth();
  const [open, setOpen] = React.useState(false);
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const handleLogout = async () => {
    try {
      await fetch('/v1/auth/logout', { method: 'POST' });
    } catch (e) {
      console.error('Logout failed', e);
    } finally {
      setUser(null);
      toast.success('Logged out successfully');
      router.push('/');
    }
  };

  return (
    <header className={cn('sticky top-0 z-50 w-full border-b border-border transition-all duration-200', scrolled ? 'glass shadow-sm' : 'bg-card/80 backdrop-blur-sm')}>
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 lg:px-6">
        <div className="flex items-center gap-6">
          <Logo />
          <nav className="hidden items-center gap-1 md:flex">
            {navLinks.map((link) => {
              const active = pathname === link.href || pathname.startsWith(link.href + '/');
              return (
                <Link key={link.href} href={link.href} className={cn('flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors', active ? 'bg-secondary text-secondary-foreground' : 'text-muted-foreground hover:text-foreground hover:bg-muted')}>
                  <link.icon className="h-4 w-4" />
                  {link.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" className="hidden h-9 w-9 sm:flex" aria-label="Search"><Search className="h-4 w-4" /></Button>
          <ThemeToggle />
          {!isLoading && !user && (
            <div className="hidden items-center gap-2 md:flex">
              <Button variant="ghost" size="sm" asChild><Link href="/login">Sign In</Link></Button>
              <Button size="sm" asChild><Link href="/signup">Sign Up</Link></Button>
            </div>
          )}
          {!isLoading && user && (
            <div className="hidden md:block">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="flex items-center gap-2 rounded-lg p-1 transition-colors hover:bg-muted">
                    <Avatar className="h-8 w-8 border border-border">
                      <AvatarFallback className="bg-primary text-primary-foreground text-xs">{getInitials(user.name || 'User')}</AvatarFallback>
                    </Avatar>
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-56">
                  <DropdownMenuLabel>
                    <div className="flex flex-col"><span className="text-sm font-semibold">{user.name}</span><span className="text-xs text-muted-foreground">{user.email}</span></div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  {userLinks.map((link) => (
                    <DropdownMenuItem key={link.href} asChild><Link href={link.href} className="flex items-center gap-2"><link.icon className="h-4 w-4" />{link.label}</Link></DropdownMenuItem>
                  ))}
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild><Link href="/admin" className="flex items-center gap-2"><Settings className="h-4 w-4" />Admin Panel</Link></DropdownMenuItem>
                  <DropdownMenuItem onClick={handleLogout} className="flex items-center gap-2 text-destructive cursor-pointer"><LogOut className="h-4 w-4" />Sign Out</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          )}
          <Sheet open={open} onOpenChange={setOpen}>
            <SheetTrigger asChild><Button variant="ghost" size="icon" className="h-9 w-9 md:hidden"><Menu className="h-5 w-5" /></Button></SheetTrigger>
            <SheetContent side="right" className="w-[300px] sm:w-[360px]">
              <SheetTitle className="sr-only">Navigation</SheetTitle>
              <div className="mt-4 flex flex-col gap-1">
                {navLinks.map((link) => (
                  <Link key={link.href} href={link.href} onClick={() => setOpen(false)} className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground">
                    <link.icon className="h-4 w-4" />{link.label}
                  </Link>
                ))}
                {user && (
                  <>
                    <div className="my-2 h-px bg-border" />
                    <div className="px-3 py-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Account</div>
                    {userLinks.map((link) => (
                      <Link key={link.href} href={link.href} onClick={() => setOpen(false)} className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground">
                        <link.icon className="h-4 w-4" />{link.label}
                      </Link>
                    ))}
                    <Link href="/admin" onClick={() => setOpen(false)} className="flex items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground">
                      <Settings className="h-4 w-4" />Admin Panel
                    </Link>
                    <div className="my-2 h-px bg-border" />
                    <div className="flex flex-col gap-2 px-3">
                      <Button variant="outline" onClick={() => { handleLogout(); setOpen(false); }}>Sign Out</Button>
                    </div>
                  </>
                )}
                {!user && (
                  <>
                    <div className="my-2 h-px bg-border" />
                    <div className="flex flex-col gap-2 px-3">
                      <Button variant="outline" asChild><Link href="/login" onClick={() => setOpen(false)}>Sign In</Link></Button>
                      <Button asChild><Link href="/signup" onClick={() => setOpen(false)}>Sign Up</Link></Button>
                    </div>
                  </>
                )}
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </header>
  );
}
