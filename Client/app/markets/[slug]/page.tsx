'use client';

import * as React from 'react';
import { use } from 'react';
import { SiteLayout } from '@/components/layout/site-layout';
import { TradePanel } from '@/components/trading/trade-panel';
import { OrderBook } from '@/components/trading/order-book';
import { TradeHistory } from '@/components/trading/trade-history';
import { ProbabilityBar } from '@/components/shared/probability-bar';
import { CategoryBadge } from '@/components/shared/category-badge';
import { StatusBadge } from '@/components/shared/status-badge';
import { AIRecommendationCard } from '@/components/ai/recommendation-card';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { LineChart } from '@/components/charts/market-charts';
import { getRecommendationByMarket } from '@/lib/mock-data';
import { fetchMarketBySlug } from '@/lib/api';
import type { Market } from '@/lib/types';
import { formatCurrency, formatNumber, getTimeLeft, formatPrice } from '@/lib/format';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import { Users, TrendingUp, Clock, ExternalLink, Brain, ArrowLeft, Network, CheckCircle2 } from 'lucide-react';

export default function MarketDetailPage({ params }: { params: { slug: string } }) {
  const { slug } = params;
  const [timeframe, setTimeframe] = React.useState<'7d' | '30d' | '90d'>('30d');
  const [market, setMarket] = React.useState<Market | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    setLoading(true);
    fetchMarketBySlug(slug, timeframe)
      .then(data => {
        setMarket(data);
        setLoading(false);
      })
      .catch(() => {
        setMarket(null);
        setLoading(false);
      });
  }, [slug, timeframe]);

  if (loading) {
    return (
      <SiteLayout>
        <div className="flex min-h-[50vh] items-center justify-center">
          <div className="text-muted-foreground">Loading market details...</div>
        </div>
      </SiteLayout>
    );
  }

  if (!market) notFound();

  const yes = market.outcomes?.[0] || { price: 50 };
  const no = market.outcomes?.[1] || { price: 50 };
  const aiRec = getRecommendationByMarket(slug);
  const chartData = market.priceHistory || [];

  return (
    <SiteLayout>
      <div className="mx-auto max-w-7xl px-4 py-6 lg:px-6">
        <Link href="/markets" className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="h-4 w-4" /> Back to Markets</Link>
        <div className="mb-6 flex flex-col gap-4">
          <div className="flex items-center gap-2"><CategoryBadge category={market.category} /><StatusBadge status={market.status} /></div>
          <h1 className="font-display text-2xl font-bold leading-tight sm:text-3xl">{market.question}</h1>
          <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            <span className="flex items-center gap-1"><Users className="h-4 w-4" /> {formatNumber(market.traderCount, true)} traders</span>
            <span className="flex items-center gap-1"><TrendingUp className="h-4 w-4" /> {formatCurrency(market.totalVolume, { compact: true })} volume</span>
            <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> {getTimeLeft(market.endDate)}</span>
          </div>
        </div>
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 lg:col-span-2">
            <Card className="p-5">
              <div className="mb-4 flex items-center justify-between">
                <div><h3 className="font-semibold">Price History</h3><p className="text-sm text-muted-foreground">YES/NO probability over time</p></div>
                <div className="flex rounded-lg border border-border p-0.5">
                  {(['7d', '30d', '90d'] as const).map((tf) => (
                    <button key={tf} onClick={() => setTimeframe(tf)} className={`rounded-md px-3 py-1 text-xs font-medium transition-colors ${timeframe === tf ? 'bg-primary text-primary-foreground' : 'text-muted-foreground'}`}>{tf}</button>
                  ))}
                </div>
              </div>
              <LineChart data={chartData} xKey="t" lines={[{ key: 'yes', color: 'hsl(142 62% 42%)', name: 'YES' }, { key: 'no', color: 'hsl(0 72% 51%)', name: 'NO' }]} height={300} yFormatter={(v) => `${v.toFixed(0)}%`} referenceLine={{ y: 50, label: '50%' }} />
            </Card>
            <Card className="p-5">
              <h3 className="mb-4 font-semibold">Current Probability</h3>
              <div className="mb-3 flex items-baseline justify-between">
                <div><span className="text-3xl font-bold text-success">{formatPrice(yes.price)}</span><span className="ml-2 text-sm text-muted-foreground">YES</span></div>
                <div className="text-right"><span className="text-3xl font-bold text-destructive">{formatPrice(no.price)}</span><span className="ml-2 text-sm text-muted-foreground">NO</span></div>
              </div>
              <ProbabilityBar yesPrice={yes.price} noPrice={no.price} size="lg" />
            </Card>
            <Card className="p-5">
              <h3 className="mb-3 font-semibold">About this market</h3>
              <p className="text-sm leading-relaxed text-muted-foreground">{market.description}</p>
              {market.resolutionSource && (
                <div className="mt-4 flex items-center gap-2 rounded-lg bg-muted/50 p-3 text-sm">
                  <ExternalLink className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Resolution Source:</span><span className="font-medium">{market.resolutionSource}</span>
                </div>
              )}
              <div className="mt-4 flex flex-wrap gap-2">{market.tags.map((tag) => <span key={tag} className="rounded-full bg-secondary px-3 py-1 text-xs font-medium text-secondary-foreground">{tag}</span>)}</div>
            </Card>
            {aiRec && (
              <div>
                <div className="mb-3 flex items-center gap-2"><Brain className="h-5 w-5 text-primary" /><h3 className="font-display text-lg font-bold">AI Analysis</h3></div>
                <AIRecommendationCard recommendation={aiRec} />
              </div>
            )}
          </div>
          <div className="space-y-6">
            <TradePanel market={market} />
            <OrderBook slug={market.slug} />
            <TradeHistory slug={market.slug} />
            
            <Card className="p-5">
              <div className="mb-4 flex items-center gap-2">
                <Network className="h-4 w-4 text-primary" />
                <h3 className="font-semibold">Exchange Liquidity</h3>
              </div>
              <div className="space-y-4 text-sm">
                <div className="flex items-center justify-between rounded-lg border border-border p-3">
                  <div className="flex items-center gap-2">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-chart-1/20 text-chart-1">P</div>
                    <span className="font-medium">Polymarket</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">$1.2M</span>
                    <CheckCircle2 className="h-4 w-4 text-success" />
                  </div>
                </div>
                <div className="flex items-center justify-between rounded-lg border border-border p-3">
                  <div className="flex items-center gap-2">
                    <div className="flex h-6 w-6 items-center justify-center rounded-full bg-chart-2/20 text-chart-2">K</div>
                    <span className="font-medium">Kalshi</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">$840K</span>
                    <CheckCircle2 className="h-4 w-4 text-success" />
                  </div>
                </div>
                <p className="text-xs text-muted-foreground text-center">Smart routing optimizes execution across these venues.</p>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </SiteLayout>
  );
}
