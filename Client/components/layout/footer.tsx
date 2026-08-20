import Link from 'next/link';
import { Logo } from '@/components/shared/logo';
import { Github, Twitter, Send, Shield, TrendingUp } from 'lucide-react';

const footerLinks = [
  { title: 'Platform', links: [{ label: 'Markets', href: '/markets' }, { label: 'AI Recommendations', href: '/ai-recommendations' }, { label: 'Dashboard', href: '/dashboard' }] },
  { title: 'Account', links: [{ label: 'Sign In', href: '/login' }, { label: 'Sign Up', href: '/signup' }, { label: 'Wallet', href: '/dashboard/wallet' }, { label: 'Positions', href: '/dashboard/positions' }] },
  { title: 'Resources', links: [{ label: 'How It Works', href: '/markets' }, { label: 'Trading Guide', href: '/markets' }, { label: 'FAQ', href: '/markets' }, { label: 'API Docs', href: '/markets' }] },
  { title: 'Legal', links: [{ label: 'Terms of Service', href: '#' }, { label: 'Privacy Policy', href: '#' }, { label: 'Risk Disclosure', href: '#' }, { label: 'Responsible Trading', href: '#' }] },
];

export function Footer() {
  return (
    <footer className="border-t border-border bg-card/50">
      <div className="mx-auto max-w-7xl px-4 py-12 lg:px-6">
        <div className="grid gap-8 lg:grid-cols-5">
          <div className="lg:col-span-1">
            <Logo />
            <p className="mt-4 text-sm text-muted-foreground">Trade on real-world events with real payouts. Predict the future, one market at a time.</p>
            <div className="mt-4 flex items-center gap-3">
              <Link href="#" className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors hover:text-foreground hover:border-foreground/30" aria-label="Twitter"><Twitter className="h-4 w-4" /></Link>
              <Link href="#" className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors hover:text-foreground hover:border-foreground/30" aria-label="GitHub"><Github className="h-4 w-4" /></Link>
              <Link href="#" className="flex h-8 w-8 items-center justify-center rounded-lg border border-border text-muted-foreground transition-colors hover:text-foreground hover:border-foreground/30" aria-label="Telegram"><Send className="h-4 w-4" /></Link>
            </div>
          </div>
          {footerLinks.map((section) => (
            <div key={section.title}>
              <h3 className="text-sm font-semibold">{section.title}</h3>
              <ul className="mt-4 space-y-2">
                {section.links.map((link) => (
                  <li key={link.label}><Link href={link.href} className="text-sm text-muted-foreground transition-colors hover:text-foreground">{link.label}</Link></li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-10 flex flex-col items-center justify-between gap-4 border-t border-border pt-6 sm:flex-row">
          <p className="text-xs text-muted-foreground">&copy; {new Date().getFullYear()} Santibet. All rights reserved. For entertainment purposes only.</p>
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><Shield className="h-3.5 w-3.5 text-primary" /> Provably Fair</span>
            <span className="flex items-center gap-1"><TrendingUp className="h-3.5 w-3.5 text-primary" /> Real-time Data</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
