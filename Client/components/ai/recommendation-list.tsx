import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { AIRecommendationCard } from '@/components/ai/recommendation-card';
import { aiRecommendations } from '@/lib/mock-data';
import type { AIRecommendation } from '@/lib/types';
import { Brain } from 'lucide-react';

export function AIRecommendationList({ recommendations: data = aiRecommendations, className, compact }: { recommendations?: AIRecommendation[]; className?: string; compact?: boolean }) {
  return <div className={cn('grid gap-4 sm:grid-cols-2 lg:grid-cols-3', className)}>{data.map((rec) => <AIRecommendationCard key={rec.id} recommendation={rec} compact={compact} />)}</div>;
}

export function AIInsightBanner({ className }: { className?: string }) {
  return (
    <Card className={cn('relative overflow-hidden p-6', className)}>
      <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-transparent to-chart-2/10" />
      <div className="relative flex items-center gap-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-chart-2 text-primary-foreground"><Brain className="h-7 w-7" /></div>
        <div className="flex-1"><h2 className="font-display text-lg font-bold">AI-Powered Predictions</h2><p className="mt-1 text-sm text-muted-foreground">Get data-driven market recommendations powered by advanced models analyzing on-chain data, sentiment, and historical patterns.</p></div>
      </div>
    </Card>
  );
}
