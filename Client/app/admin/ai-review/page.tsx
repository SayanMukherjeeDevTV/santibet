'use client';

import * as React from 'react';
import { DashboardLayout } from '@/components/layout/dashboard-layout';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { fetchAiReviewQueue, approveAiReview, rejectAiReview } from '@/lib/api';
import { Brain, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { aiRecommendations as mockData } from '@/lib/mock-data';

export default function AIReviewPage() {
  const [pendingItems, setPendingItems] = React.useState<any[]>([]);

  React.useEffect(() => {
    fetchAiReviewQueue()
      .then(data => {
        if (data && data.length > 0) {
          setPendingItems(data);
        } else {
          setPendingItems(mockData);
        }
      })
      .catch(console.error);
  }, []);

    const handleApprove = async (id: string, type: string = 'recommendation') => {
    try {
      await approveAiReview(type, id);
      setPendingItems((prev) => prev.filter((prevItem) => {
        const isRealData = 'itemType' in prevItem;
        const itemType = isRealData ? prevItem.itemType : 'recommendation';
        const itemId = isRealData 
          ? (itemType === 'market_draft' ? prevItem.marketDraft.id : prevItem.recommendation.id)
          : prevItem.id;
        return itemId !== id;
      }));
      toast.success('AI item approved and published');
    } catch (e) {
      toast.error('Failed to approve item');
    }
  };

  const handleReject = async (id: string, type: string = 'recommendation') => {
    try {
      await rejectAiReview(type, id);
      setPendingItems((prev) => prev.filter((prevItem) => {
        const isRealData = 'itemType' in prevItem;
        const itemType = isRealData ? prevItem.itemType : 'recommendation';
        const itemId = isRealData 
          ? (itemType === 'market_draft' ? prevItem.marketDraft.id : prevItem.recommendation.id)
          : prevItem.id;
        return itemId !== id;
      }));
      toast.error('AI item rejected');
    } catch (e) {
      toast.error('Failed to reject item');
    }
  };


  return (
    <DashboardLayout variant="admin">
      <div className="space-y-6 p-6">
        <div>
          <div className="flex items-center gap-2">
            <Brain className="h-6 w-6 text-primary" />
            <h1 className="font-display text-2xl font-bold">AI Review Panel</h1>
          </div>
          <p className="mt-1 text-sm text-muted-foreground">Review, approve, or reject AI-generated markets and recommendations before they go live.</p>
        </div>

        <div className="grid gap-6">
          {pendingItems.length === 0 ? (
            <Card className="flex flex-col items-center justify-center py-12">
              <CheckCircle2 className="h-12 w-12 text-success mb-4" />
              <h3 className="text-lg font-semibold">All caught up!</h3>
              <p className="text-sm text-muted-foreground">There are no pending AI items to review.</p>
            </Card>
          ) : (
            pendingItems.map((queueItem) => {
              // Unwrap the real backend data or fallback to the mock data format
              const isRealData = 'itemType' in queueItem;
              const type = isRealData ? queueItem.itemType : 'recommendation';
              const item = isRealData 
                ? (type === 'market_draft' ? queueItem.marketDraft : queueItem.recommendation)
                : queueItem;
              
              const isDraft = type === 'market_draft';

              return (
              <Card key={item.id} className="p-5">
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="border-primary text-primary">
                        {isDraft ? "Market Draft" : "Recommendation"}
                      </Badge>
                      <span className="text-xs text-muted-foreground">Pending Review</span>
                    </div>
                    <h3 className="font-semibold text-lg">{item.question}</h3>
                    <p className="text-sm text-muted-foreground max-w-3xl">
                      {isDraft ? item.description : item.reasoning}
                    </p>
                    
                    {!isDraft && (
                      <div className="flex items-center gap-4 text-sm">
                        <div className="flex items-center gap-1">
                          <span className="text-muted-foreground">Outcome:</span>
                          <span className={item.outcome === 'YES' ? 'text-success font-medium' : 'text-destructive font-medium'}>Buy {item.outcome}</span>
                        </div>
                        <div className="flex items-center gap-1">
                          <span className="text-muted-foreground">Confidence:</span>
                          <span className="font-medium">{item.confidence}%</span>
                        </div>
                      </div>
                    )}
                    
                    {isDraft && (
                      <div className="flex flex-col gap-1 text-sm text-muted-foreground">
                         <p><strong>Category:</strong> {item.category}</p>
                         <p><strong>Criteria:</strong> {item.resolution_criteria}</p>
                      </div>
                    )}

                  </div>
                  <div className="flex gap-2 sm:flex-col min-w-[120px]">
                    <Button onClick={() => handleApprove(item.id, type)} className="flex-1 bg-success hover:bg-success/90">
                      <CheckCircle2 className="h-4 w-4 mr-2" /> Approve
                    </Button>
                    <Button onClick={() => handleReject(item.id, type)} variant="outline" className="flex-1 text-destructive hover:text-destructive hover:bg-destructive/10">
                      <XCircle className="h-4 w-4 mr-2" /> Reject
                    </Button>
                  </div>
                </div>
              </Card>
            )})
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
