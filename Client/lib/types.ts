export type MarketCategory = 'politics' | 'crypto' | 'sports' | 'economy' | 'entertainment' | 'technology' | 'world';
export type MarketStatus = 'active' | 'upcoming' | 'resolved';
export type MarketOutcome = 'YES' | 'NO';

export interface MarketOutcomeData {
  id: string;
  label: string;
  price: number;
  probability: number;
  volume: number;
  priceHistory: { t: string; price: number }[];
}

export interface Market {
  id: string;
  slug: string;
  question: string;
  category: MarketCategory;
  status: MarketStatus;
  endDate: string;
  liquidity: number;
  totalVolume: number;
  volume24h: number;
  traderCount: number;
  image?: string;
  outcomes: MarketOutcomeData[];
  priceHistory: { t: string; yes: number; no: number }[];
  tags: string[];
  description: string;
  resolutionSource?: string;
  featured?: boolean;
  sparklineData: { t: string; v: number }[];
}

export type PositionStatus = 'open' | 'won' | 'lost' | 'sold';

export interface Position {
  id: string;
  marketId: string;
  marketSlug: string;
  question: string;
  outcome: MarketOutcome;
  shares: number;
  avgPrice: number;
  currentPrice: number;
  invested: number;
  currentValue: number;
  pnl: number;
  pnlPercent: number;
  status: PositionStatus;
  openedAt: string;
}

export interface Transaction {
  id: string;
  type: 'deposit' | 'withdrawal' | 'buy' | 'sell' | 'payout' | 'fee';
  marketId?: string;
  marketSlug?: string;
  question?: string;
  amount: number;
  balanceAfter: number;
  status: 'completed' | 'pending' | 'failed';
  createdAt: string;
}

export interface OrderBookEntry {
  price: number;
  size: number;
  total: number;
}

export interface TradeHistoryEntry {
  id: string;
  price: number;
  size: number;
  outcome: MarketOutcome;
  time: string;
  side: 'buy' | 'sell';
}

export interface User {
  id: string;
  name: string;
  email: string;
  avatarUrl: string;
  balance: number;
  portfolioValue: number;
  totalPnl: number;
  totalPnlPercent: number;
  rank: number;
  joinedAt: string;
  verified: boolean;
  role: string;
}

export interface LeaderboardEntry {
  rank: number;
  userId: string;
  name: string;
  avatarUrl: string;
  portfolioValue: number;
  totalPnl: number;
  totalPnlPercent: number;
  volume: number;
  marketsTraded: number;
  winRate: number;
}

export interface AIRecommendation {
  id: string;
  marketId: string;
  marketSlug: string;
  question: string;
  category: MarketCategory;
  outcome: MarketOutcome;
  confidence: number;
  currentPrice: number;
  targetPrice: number;
  expectedReturn: number;
  reasoning: string;
  riskLevel: 'low' | 'medium' | 'high';
  timeframe: string;
  signals: { label: string; value: string; positive: boolean }[];
  createdAt: string;
}

export interface AdminMarket {
  id: string;
  question: string;
  category: MarketCategory;
  status: MarketStatus;
  volume: number;
  traderCount: number;
  createdAt: string;
  reported: boolean;
  featured?: boolean;
}

export interface AdminUser {
  id: string;
  name: string;
  email: string;
  balance: number;
  volume: number;
  status: 'active' | 'suspended' | 'banned';
  joinedAt: string;
  verified: boolean;
}

export interface CategoryInfo {
  id: string; // Changed from MarketCategory to string because backend IDs can be generic strings
  name?: string;
  label: string;
  icon: string;
  color: string;
  description: string;
}

export interface AuditLogEntry {
  id: number;
  actorUserId?: string | null;
  adminId?: string | null;
  action: string;
  targetType?: string | null;
  targetId?: string | null;
  before?: any;
  after?: any;
  details?: any;
  ip?: string | null;
  ipAddress?: string | null;
  createdAt: string;
}
