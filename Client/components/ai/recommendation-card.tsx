import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { CategoryBadge } from '@/components/shared/category-badge';
import { GaugeChart } from '@/components/charts/market-charts';
import { formatPrice, formatPercent } from '@/lib/format';
import type { AIRecommendation } from '@/lib/types';
import { Sparkles, TrendingUp, Clock, CheckCircle2, XCircle } from 'lucide-react';

const riskColors = { low: 'text-success bg-success/10', medium: 'text-warning bg-warning/10', high: 'text-destructive bg-destructive/10' };

export function AIRecommendationCard({ recommendation: rec, className, compact }: { recommendation: AIRecommendation; className?: string; compact?: boolean }) {
  return (
    <Card className={cn('relative overflow-hidden p-5 transition-all hover:shadow-lg', className)}>
      <div className="absolute right-0 top-0 h-24 w-24 rounded-full bg-primary/5 blur-2xl" />
      <div className="relative">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-bold text-primary"><Sparkles className="h-3 w-3" /> AI PICK</span>
            <CategoryBadge category={rec.category} />
          </div>
          <span className={cn('rounded-full px-2 py-0.5 text-xs font-medium capitalize', riskColors[rec.riskLevel])}>{rec.riskLevel} risk</span>
        </div>
        <Link href={`/markets/${rec.marketSlug}`}><h3 className="mt-3 line-clamp-2 text-sm font-semibold hover:text-primary">{rec.question}</h3></Link>
        <div className="mt-4 flex items-center gap-4">
          <div className="flex flex-col items-center">
            <div className="relative h-[72px] w-[72px]">
              <GaugeChart value={rec.confidence} height={72} color={rec.confidence >= 70 ? 'hsl(142 62% 42%)' : rec.confidence >= 50 ? 'hsl(38 92% 55%)' : 'hsl(0 72% 51%)'} />
              <div className="absolute inset-0 flex items-center justify-center"><span className="font-display text-lg font-bold">{rec.confidence}%</span></div>
            </div>
            <span className="text-xs text-muted-foreground">Confidence</span>
          </div>
          <div className="flex-1 space-y-2">
            <div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Recommendation</span><span className={cn('font-bold', rec.outcome === 'YES' ? 'text-success' : 'text-destructive')}>{rec.outcome === 'YES' ? 'Buy YES' : 'Buy NO'}</span></div>
            <div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Current Price</span><span className="tabular-nums font-medium">{formatPrice(rec.currentPrice)}</span></div>
            <div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Target Price</span><span className="tabular-nums font-medium text-primary">{formatPrice(rec.targetPrice)}</span></div>
            <div className="flex items-center justify-between text-sm"><span className="text-muted-foreground">Expected Return</span><span className="font-bold text-success">{formatPercent(rec.expectedReturn)}</span></div>
          </div>
        </div>
        {!compact && <p className="mt-4 line-clamp-3 text-sm text-muted-foreground">{rec.reasoning}</p>}
        {!compact && (
          <div className="mt-4 grid grid-cols-2 gap-2">
            {rec.signals.map((s, i) => (
              <div key={i} className="flex items-center gap-2 rounded-lg bg-muted/50 p-2 text-xs">
                {s.positive ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-success" /> : <XCircle className="h-3.5 w-3.5 shrink-0 text-destructive" />}
                <span className="text-muted-foreground">{s.label}</span><span className="ml-auto font-medium">{s.value}</span>
              </div>
            ))}
          </div>
        )}
        <div className="mt-4 flex items-center justify-between">
          <span className="flex items-center gap-1 text-xs text-muted-foreground"><Clock className="h-3 w-3" /> {rec.timeframe}</span>
          <Button size="sm" asChild><Link href={`/markets/${rec.marketSlug}`}><TrendingUp className="h-3.5 w-3.5 mr-1" /> Trade</Link></Button>
        </div>
      </div>
    </Card>
  );
}
