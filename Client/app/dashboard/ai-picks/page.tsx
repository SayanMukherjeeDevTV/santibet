export const dynamic = 'force-dynamic';

import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { AIRecommendationList } from '@/components/ai/recommendation-list';
import { AIInsightBanner } from '@/components/ai/recommendation-list';
import { aiRecommendations as mockData } from '@/lib/mock-data';
import { fetchAIRecommendations } from '@/lib/api';

export default async function DashboardAIPicksPage() {
  let aiRecommendations = mockData;
  try {
    const data = await fetchAIRecommendations();
    if (Array.isArray(data) && data.length > 0) {
      aiRecommendations = data;
    }
  } catch (e) {
    console.error(e);
  }

  return (
    <DashboardLayout>
      <div className="space-y-6 p-6">
        <div><h1 className="font-display text-2xl font-bold">AI Picks for You</h1><p className="mt-1 text-sm text-muted-foreground">Personalized AI recommendations based on your trading history</p></div>
        <AIInsightBanner />
        <AIRecommendationList recommendations={aiRecommendations} />
      </div>
    </DashboardLayout>
  );
}
