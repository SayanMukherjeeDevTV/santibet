export const dynamic = 'force-dynamic';

import { SiteLayout } from '@/components/layout/site-layout';
import { AIRecommendationList, AIInsightBanner } from '@/components/ai/recommendation-list';
import { StatCard } from '@/components/shared/stat-card';
import { aiRecommendations as mockData } from '@/lib/mock-data';
import { fetchAIRecommendations } from '@/lib/api';
import { Brain, Target, Sparkles, TrendingUp } from 'lucide-react';

export default async function AIRecommendationsPage() {
  let aiRecommendations = mockData;
  try {
    const data = await fetchAIRecommendations();
    if (Array.isArray(data) && data.length > 0) {
      aiRecommendations = data;
    }
  } catch (e) {
    console.error(e);
  }

  const avgConfidence = Math.round(aiRecommendations.reduce((s, r) => s + r.confidence, 0) / (aiRecommendations.length || 1));
  const avgReturn = (aiRecommendations.reduce((s, r) => s + r.expectedReturn, 0) / (aiRecommendations.length || 1)).toFixed(1);

  return (
    <SiteLayout>
      <div className="mx-auto max-w-7xl px-4 py-8 lg:px-6">
        <div className="mb-6">
          <div className="flex items-center gap-2"><Brain className="h-6 w-6 text-primary" /><h1 className="font-display text-3xl font-bold">AI Recommendations</h1></div>
          <p className="mt-1 text-muted-foreground">Data-driven market predictions powered by advanced AI models</p>
        </div>
        <div className="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard label="Active Picks" value={String(aiRecommendations.length)} icon={Sparkles} />
          <StatCard label="Avg Confidence" value={`${avgConfidence}%`} icon={Target} iconColor="text-chart-2" />
          <StatCard label="Avg Expected Return" value={`+${avgReturn}%`} icon={TrendingUp} iconColor="text-success" />
          <StatCard label="Model Version" value="v2.4.1" icon={Brain} iconColor="text-chart-3" />
        </div>
        <div className="mb-6"><AIInsightBanner /></div>
        <AIRecommendationList recommendations={aiRecommendations} />
      </div>
    </SiteLayout>
  );
}
