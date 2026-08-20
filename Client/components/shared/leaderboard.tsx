import Link from 'next/link';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { getInitials } from '@/lib/format';
import { leaderboard } from '@/lib/mock-data';
import type { LeaderboardEntry } from '@/lib/types';
import { Trophy, Medal } from 'lucide-react';

function RankBadge({ rank }: { rank: number }) {
  if (rank === 1) return <Medal className="h-5 w-5 text-yellow-500" />;
  if (rank === 2) return <Medal className="h-5 w-5 text-slate-300" />;
  if (rank === 3) return <Medal className="h-5 w-5 text-amber-600" />;
  return <span className="font-display text-sm font-bold text-muted-foreground">#{rank}</span>;
}

export function Leaderboard({ entries = leaderboard, className, limit }: { entries?: LeaderboardEntry[]; className?: string; limit?: number }) {
  const sortedEntries = [...entries].sort((a, b) => b.portfolioValue - a.portfolioValue);
  const rows = limit ? sortedEntries.slice(0, limit) : sortedEntries;
  
  return (
    <Card className={cn('p-0', className)}>
      <div className="flex items-center gap-2 border-b p-4">
        <Trophy className="h-5 w-5 text-primary" />
        <h3 className="font-semibold">Top Traders</h3>
      </div>
      <div className="divide-y">
        {rows.map((entry, index) => {
          const displayRank = index + 1;
          return (
            <Link key={entry.userId} href="/dashboard" className={cn('flex items-center gap-4 p-4 transition-colors hover:bg-muted/50', displayRank <= 3 && 'bg-primary/5')}>
              <div className="flex w-8 items-center justify-center"><RankBadge rank={displayRank} /></div>
              <Avatar className="h-10 w-10"><AvatarImage src={entry.avatarUrl} /><AvatarFallback>{getInitials(entry.name)}</AvatarFallback></Avatar>
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-semibold">{entry.name}</div>
                <div className="text-xs text-muted-foreground">{entry.marketsTraded} markets · {entry.winRate}% win rate</div>
              </div>
            </Link>
          );
        })}
      </div>
    </Card>
  );
}
