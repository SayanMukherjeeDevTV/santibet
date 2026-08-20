'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { SiteLayout } from '@/components/layout/site-layout';
import { FeaturedMarket } from '@/components/market/featured-market';
import { MarketGrid } from '@/components/market/market-grid';
import { StatCard } from '@/components/shared/stat-card';
import { Leaderboard } from '@/components/shared/leaderboard';
import { AIRecommendationCard } from '@/components/ai/recommendation-card';
import { Button } from '@/components/ui/button';
import { markets, aiRecommendations } from '@/lib/mock-data';
import { fetchStats, fetchFeaturedMarkets, fetchCategories, fetchMarkets, fetchLeaderboard, fetchAIRecommendations } from '@/lib/api';
import { formatCurrency, formatNumber } from '@/lib/format';
import { TrendingUp, Users, BarChart3, DollarSign, ArrowRight, Brain, Zap, Shield, Activity, Trophy } from 'lucide-react';
import { useAuth } from '@/components/auth-context';
import type { Market, CategoryInfo } from '@/lib/types';

export default function HomePage() {
  const { user, isLoading: isAuthLoading } = useAuth();

  const [platformStats, setPlatformStats] = useState<any>(null);
  const [categories, setCategories] = useState<CategoryInfo[]>([]);
  
  const [featured, setFeatured] = useState<Market[]>([]);
  const [topMarkets, setTopMarkets] = useState<Market[]>([]);
  const [leaderboardData, setLeaderboardData] = useState<any[]>([]);
  const [topRecs, setTopRecs] = useState<any[]>([]);

  useEffect(() => {
    fetchStats().then(setPlatformStats).catch(() => {});
    fetchCategories().then(setCategories).catch(() => {});
  }, []);

  useEffect(() => {
    if (isAuthLoading) return;

    if (user) {
      // User logged in: fetch and show actual data
      fetchFeaturedMarkets().then(setFeatured).catch(() => setFeatured([]));
      
      fetchMarkets().then(data => {
        setTopMarkets(data?.items?.slice(0, 6) || []);
      }).catch(() => setTopMarkets([]));
      
      fetchLeaderboard().then(setLeaderboardData).catch(() => setLeaderboardData([]));
      
      fetchAIRecommendations().then(data => {
        if (Array.isArray(data)) {
          setTopRecs(data.slice(0, 3));
        } else if (data?.items && Array.isArray(data.items)) {
          setTopRecs(data.items.slice(0, 3));
        } else {
          setTopRecs([]);
        }
      }).catch(() => setTopRecs([]));
    } else {
      // User not logged in: show mock data
      setFeatured(markets.filter(m => m.featured).slice(0, 2));
      setTopMarkets(markets.slice(0, 6));
      setTopRecs(aiRecommendations.slice(0, 3));
      setLeaderboardData([]);
    }
  }, [user, isAuthLoading]);

  return (
    <SiteLayout>
      <section className="relative overflow-hidden border-b border-border">
        <div className="absolute inset-0 bg-grid opacity-30" />
        <div className="absolute left-1/2 top-0 h-[400px] w-[600px] -translate-x-1/2 rounded-full bg-primary/10 blur-[120px]" />
        <div className="relative mx-auto max-w-7xl px-4 py-16 lg:px-6 lg:py-24">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-1.5 text-sm font-medium">
              <Zap className="h-4 w-4 text-primary" /> Trade on the future. Real events, real payouts.
            </span>
            <h1 className="mt-6 font-display text-4xl font-bold tracking-tight text-balance sm:text-5xl lg:text-6xl">
              Predict the future.<br />
              <span className="bg-gradient-to-r from-primary to-chart-2 bg-clip-text text-transparent">Profit from what you know.</span>
            </h1>
            <p className="mt-6 text-lg text-muted-foreground text-balance">Santibet is a modern prediction market platform. Trade on politics, crypto, sports, and world events with AI-powered insights and real-time trading.</p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Button size="lg" asChild><Link href="/markets">Start Trading <ArrowRight className="ml-2 h-4 w-4" /></Link></Button>
              <Button size="lg" variant="outline" asChild><Link href="/ai-recommendations"><Brain className="mr-2 h-4 w-4" /> AI Picks</Link></Button>
            </div>
          </div>
          <div className="mt-16 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Total Volume" value={formatCurrency(platformStats?.totalVolume || 0, { compact: true })} icon={TrendingUp} change={12.4} />
            <StatCard label="Active Traders" value={formatNumber(platformStats?.totalTraders || 0, true)} icon={Users} change={8.2} />
            <StatCard label="Open Markets" value={String(platformStats?.activeMarkets || 0)} icon={BarChart3} change={5.1} />
            <StatCard label="Total Markets" value={String(platformStats?.totalMarkets || 0)} icon={DollarSign} change={15.7} />
          </div>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 lg:px-6">
        <div className="mb-6 flex items-end justify-between">
          <div><h2 className="font-display text-2xl font-bold">Featured Markets</h2><p className="mt-1 text-sm text-muted-foreground">High-activity markets with the most trading volume</p></div>
          <Button variant="ghost" asChild><Link href="/markets">View All <ArrowRight className="ml-1 h-4 w-4" /></Link></Button>
        </div>
        {featured.length > 0 ? (
          <div className="grid gap-4 lg:grid-cols-2">{featured.slice(0, 2).map((m) => <FeaturedMarket key={m.id} market={m} />)}</div>
        ) : (
          <p className="text-muted-foreground">No featured markets right now.</p>
        )}
      </section>

      <section className="mx-auto max-w-7xl px-4 py-6 lg:px-6">
        <div className="mb-4 flex items-center gap-2"><Activity className="h-5 w-5 text-primary" /><h2 className="font-display text-xl font-bold">Browse by Category</h2></div>
        {categories.length > 0 ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-7">
            {categories.map((cat) => (
              <Link key={cat.id} href={`/markets?category=${cat.id}`} className="group flex flex-col items-center gap-2 rounded-xl border border-border p-4 transition-all hover:border-primary/40 hover:shadow-md">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary transition-transform group-hover:scale-110"><span className="text-lg font-bold">{cat.name?.charAt(0) || cat.label?.charAt(0) || 'C'}</span></div>
                <span className="text-xs font-medium">{cat.name || cat.label}</span>
              </Link>
            ))}
          </div>
        ) : (
          <p className="text-muted-foreground">No categories found.</p>
        )}
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 lg:px-6">
        <div className="mb-6 flex items-end justify-between"><div><h2 className="font-display text-2xl font-bold">Trending Markets</h2><p className="mt-1 text-sm text-muted-foreground">Most actively traded markets right now</p></div></div>
        {topMarkets.length > 0 ? (
          <MarketGrid markets={topMarkets} />
        ) : (
          <p className="text-muted-foreground">No trending markets right now.</p>
        )}
      </section>

      <section className="mx-auto max-w-7xl px-4 py-12 lg:px-6">
        <div className="grid gap-6 lg:grid-cols-3 lg:items-start">
          <div className="lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-primary" />
                <h2 className="font-display text-xl font-bold">AI Recommendations</h2>
              </div>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/ai-recommendations">View All <ArrowRight className="ml-1 h-4 w-4" /></Link>
              </Button>
            </div>
            {topRecs.length > 0 ? (
              <div className="flex flex-col gap-4">
                {topRecs.map((rec) => (
                  <AIRecommendationCard key={rec.id} recommendation={rec} />
                ))}
              </div>
            ) : (
              <p className="text-muted-foreground">No AI recommendations available.</p>
            )}
          </div>
          <div className="lg:sticky lg:top-24">
            <div className="mb-4 flex items-center gap-2"><Trophy className="h-5 w-5 text-primary" /><h2 className="font-display text-xl font-bold">Top Traders</h2></div>
            {leaderboardData && leaderboardData.length > 0 ? (
              <Leaderboard entries={leaderboardData} limit={5} />
            ) : (
              <p className="text-muted-foreground">No top traders available.</p>
            )}
          </div>
        </div>
      </section>

      <section className="border-t border-border bg-card/30">
        <div className="mx-auto max-w-4xl px-4 py-16 text-center lg:px-6">
          <Shield className="mx-auto h-12 w-12 text-primary" />
          <h2 className="mt-4 font-display text-3xl font-bold">Ready to start trading?</h2>
          <p className="mt-3 text-muted-foreground">Join thousands of traders predicting the future and earning real payouts.</p>
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <Button size="lg" asChild><Link href="/signup">Create Free Account</Link></Button>
            <Button size="lg" variant="outline" asChild><Link href="/markets">Explore Markets</Link></Button>
          </div>
        </div>
      </section>
    </SiteLayout>
  );
}

