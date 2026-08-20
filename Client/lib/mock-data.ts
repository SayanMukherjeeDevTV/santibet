import type {
  Market, Position, Transaction, User, LeaderboardEntry, AIRecommendation,
  TradeHistoryEntry, OrderBookEntry, AdminMarket, AdminUser, CategoryInfo,
} from './types';

export const categories: CategoryInfo[] = [
  { id: 'politics', label: 'Politics', icon: 'Landmark', color: 'text-chart-1', description: 'Elections, policy, and government' },
  { id: 'crypto', label: 'Crypto', icon: 'Bitcoin', color: 'text-chart-3', description: 'Bitcoin, Ethereum, and digital assets' },
  { id: 'sports', label: 'Sports', icon: 'Trophy', color: 'text-chart-5', description: 'Matches, tournaments, and records' },
  { id: 'economy', label: 'Economy', icon: 'TrendingUp', color: 'text-chart-2', description: 'Inflation, GDP, and markets' },
  { id: 'entertainment', label: 'Entertainment', icon: 'Clapperboard', color: 'text-chart-4', description: 'Movies, music, and awards' },
  { id: 'technology', label: 'Technology', icon: 'Cpu', color: 'text-primary', description: 'AI, gadgets, and innovation' },
  { id: 'world', label: 'World', icon: 'Globe', color: 'text-chart-2', description: 'Global events and news' },
];

function genPriceHistory(days: number, start: number, vol = 0.03) {
  const data: { t: string; yes: number; no: number }[] = [];
  let yes = start;
  for (let i = days; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    yes = Math.max(2, Math.min(98, yes + (Math.random() - 0.5) * vol * 100));
    data.push({ t: d.toISOString().split('T')[0], yes: Math.round(yes * 100) / 100, no: Math.round((100 - yes) * 100) / 100 });
  }
  return data;
}

function genSparkline(points: number, start: number) {
  const data: { t: string; v: number }[] = [];
  let v = start;
  for (let i = 0; i < points; i++) {
    v = Math.max(1, Math.min(99, v + (Math.random() - 0.5) * 4));
    data.push({ t: String(i), v: Math.round(v * 100) / 100 });
  }
  return data;
}

function genOutcomeHistory(days: number, start: number) {
  const data: { t: string; price: number }[] = [];
  let p = start;
  for (let i = days; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    p = Math.max(2, Math.min(98, p + (Math.random() - 0.5) * 3));
    data.push({ t: d.toISOString().split('T')[0], price: Math.round(p * 100) / 100 });
  }
  return data;
}

const baseMarkets: Omit<Market, 'priceHistory' | 'sparklineData' | 'outcomes'>[] = [
  { id: 'm1', slug: 'btc-100k-by-2026', question: 'Will Bitcoin reach $100,000 by end of 2026?', category: 'crypto', status: 'active', endDate: '2026-12-31', liquidity: 2840000, totalVolume: 15200000, volume24h: 890000, traderCount: 12453, tags: ['Bitcoin', 'BTC', 'Crypto'], description: 'This market resolves YES if the price of Bitcoin (BTC) reaches or exceeds $100,000 USD at any point before December 31, 2026, 23:59 UTC, as reported by CoinGecko.', resolutionSource: 'CoinGecko BTC/USD price', featured: true },
  { id: 'm2', slug: 'fed-rate-cut-december', question: 'Will the Fed cut interest rates in December 2026?', category: 'economy', status: 'active', endDate: '2026-12-18', liquidity: 1920000, totalVolume: 8400000, volume24h: 420000, traderCount: 8234, tags: ['Fed', 'Rates', 'Economy'], description: 'Resolves YES if the Federal Open Market Committee announces a rate cut at the December 2026 FOMC meeting.', resolutionSource: 'Federal Reserve official statement', featured: true },
  { id: 'm3', slug: 'gpt6-release-2026', question: 'Will OpenAI release GPT-6 before July 2027?', category: 'technology', status: 'active', endDate: '2027-07-01', liquidity: 1340000, totalVolume: 5600000, volume24h: 310000, traderCount: 6789, tags: ['AI', 'OpenAI', 'GPT'], description: 'Resolves YES if OpenAI officially releases a model named GPT-6 (or equivalent successor) before July 1, 2027.', resolutionSource: 'OpenAI official announcement', featured: true },
  { id: 'm4', slug: 'us-election-2028-democrat', question: 'Will a Democrat win the 2028 US Presidential Election?', category: 'politics', status: 'active', endDate: '2028-11-07', liquidity: 3200000, totalVolume: 18900000, volume24h: 1200000, traderCount: 21034, tags: ['Election', 'US', 'Politics'], description: 'Resolves YES if the Democratic nominee wins the 2028 US Presidential Election.', resolutionSource: 'Official election results', featured: true },
  { id: 'm5', slug: 'eth-5000-2026', question: 'Will Ethereum surpass $5,000 by end of 2026?', category: 'crypto', status: 'active', endDate: '2026-12-31', liquidity: 980000, totalVolume: 4200000, volume24h: 240000, traderCount: 5421, tags: ['Ethereum', 'ETH'], description: 'Resolves YES if ETH/USD reaches $5,000 before end of 2026.', resolutionSource: 'CoinGecko ETH/USD price' },
  { id: 'm6', slug: 'superbowl-2027-chiefs', question: 'Will the Chiefs win Super Bowl LXI (2027)?', category: 'sports', status: 'active', endDate: '2027-02-14', liquidity: 1560000, totalVolume: 7200000, volume24h: 560000, traderCount: 9876, tags: ['NFL', 'Super Bowl', 'Chiefs'], description: 'Resolves YES if the Kansas City Chiefs win Super Bowl LXI.', resolutionSource: 'NFL official results' },
  { id: 'm7', slug: 'sp500-6000-2026', question: 'Will the S&P 500 close above 6,000 in 2026?', category: 'economy', status: 'active', endDate: '2026-12-31', liquidity: 1120000, totalVolume: 4800000, volume24h: 180000, traderCount: 4321, tags: ['S&P 500', 'Stocks'], description: 'Resolves YES if the S&P 500 index closes above 6,000 on any trading day in 2026.', resolutionSource: 'S&P 500 daily close' },
  { id: 'm8', slug: 'apple-vision-pro-2', question: 'Will Apple announce Vision Pro 2 in 2026?', category: 'technology', status: 'active', endDate: '2026-12-31', liquidity: 760000, totalVolume: 2900000, volume24h: 120000, traderCount: 3456, tags: ['Apple', 'AR/VR'], description: 'Resolves YES if Apple officially announces a successor to the Vision Pro during 2026.', resolutionSource: 'Apple official event' },
  { id: 'm9', slug: 'oscars-best-picture-2027', question: 'Will a sci-fi film win Best Picture at the 2027 Oscars?', category: 'entertainment', status: 'active', endDate: '2027-03-07', liquidity: 540000, totalVolume: 2100000, volume24h: 89000, traderCount: 2341, tags: ['Oscars', 'Movies'], description: 'Resolves YES if a science fiction film wins the Academy Award for Best Picture at the 2027 ceremony.', resolutionSource: 'Academy Awards results' },
  { id: 'm10', slug: 'climate-1-5c-2026', question: 'Will 2026 be declared the hottest year on record?', category: 'world', status: 'active', endDate: '2027-01-15', liquidity: 680000, totalVolume: 2600000, volume24h: 145000, traderCount: 3876, tags: ['Climate', 'World'], description: 'Resolves YES if 2026 is declared the hottest year on record by major climate agencies.', resolutionSource: 'NOAA/NASA climate report' },
  { id: 'm11', slug: 'eu-ai-act-enforced', question: 'Will the EU AI Act be fully enforced by mid-2026?', category: 'politics', status: 'active', endDate: '2026-08-01', liquidity: 420000, totalVolume: 1500000, volume24h: 67000, traderCount: 1876, tags: ['EU', 'AI Regulation'], description: 'Resolves YES if the EU AI Act reaches full enforcement by August 1, 2026.', resolutionSource: 'EU official registry' },
  { id: 'm12', slug: 'world-cup-2026-usa', question: 'Will the USA reach the World Cup 2026 semifinals?', category: 'sports', status: 'upcoming', endDate: '2026-07-19', liquidity: 890000, totalVolume: 3800000, volume24h: 0, traderCount: 6234, tags: ['World Cup', 'Soccer', 'USA'], description: "Resolves YES if the USA men's national team reaches the semifinals of the 2026 FIFA World Cup.", resolutionSource: 'FIFA official results' },
];

export const markets: Market[] = baseMarkets.map((m) => {
  const yesPrice = Math.round((15 + Math.random() * 70) * 100) / 100;
  const noPrice = Math.round((100 - yesPrice) * 100) / 100;
  return {
    ...m,
    outcomes: [
      { id: `${m.id}-yes`, label: 'YES', price: yesPrice, probability: yesPrice, volume: Math.round(m.totalVolume * (yesPrice / 100)), priceHistory: genOutcomeHistory(90, yesPrice) },
      { id: `${m.id}-no`, label: 'NO', price: noPrice, probability: noPrice, volume: Math.round(m.totalVolume * (noPrice / 100)), priceHistory: genOutcomeHistory(90, noPrice) },
    ],
    priceHistory: genPriceHistory(90, yesPrice),
    sparklineData: genSparkline(30, yesPrice),
  };
});

export const currentUser: User = {
  id: 'u1', name: 'Alex Chen', email: 'alex.chen@santibet.io',
  avatarUrl: 'https://images.pexels.com/photos/2379004/pexels-photo-2379004.jpeg?auto=compress&cs=tinysrgb&w=200',
  balance: 12450.75, portfolioValue: 28934.50, totalPnl: 3420.80, totalPnlPercent: 13.4,  rank: 124,
  joinedAt: '2023-11-15',
  verified: true,
  role: 'user'
};

export const positions: Position[] = [
  { id: 'p1', marketId: 'm1', marketSlug: 'btc-100k-by-2026', question: 'Will Bitcoin reach $100,000 by end of 2026?', outcome: 'YES', shares: 500, avgPrice: 62, currentPrice: 68, invested: 310, currentValue: 340, pnl: 30, pnlPercent: 9.7, status: 'open', openedAt: '2026-01-10' },
  { id: 'p2', marketId: 'm4', marketSlug: 'us-election-2028-democrat', question: 'Will a Democrat win the 2028 US Presidential Election?', outcome: 'YES', shares: 1000, avgPrice: 48, currentPrice: 52, invested: 480, currentValue: 520, pnl: 40, pnlPercent: 8.3, status: 'open', openedAt: '2026-02-01' },
  { id: 'p3', marketId: 'm3', marketSlug: 'gpt6-release-2026', question: 'Will OpenAI release GPT-6 before July 2027?', outcome: 'NO', shares: 800, avgPrice: 35, currentPrice: 42, invested: 280, currentValue: 336, pnl: 56, pnlPercent: 20.0, status: 'open', openedAt: '2026-01-20' },
  { id: 'p4', marketId: 'm6', marketSlug: 'superbowl-2027-chiefs', question: 'Will the Chiefs win Super Bowl LXI (2027)?', outcome: 'YES', shares: 300, avgPrice: 22, currentPrice: 18, invested: 66, currentValue: 54, pnl: -12, pnlPercent: -18.2, status: 'open', openedAt: '2026-02-15' },
  { id: 'p5', marketId: 'm7', marketSlug: 'sp500-6000-2026', question: 'Will the S&P 500 close above 6,000 in 2026?', outcome: 'YES', shares: 2000, avgPrice: 58, currentPrice: 100, invested: 1160, currentValue: 2000, pnl: 840, pnlPercent: 72.4, status: 'won', openedAt: '2025-11-05' },
  { id: 'p6', marketId: 'm5', marketSlug: 'eth-5000-2026', question: 'Will Ethereum surpass $5,000 by end of 2026?', outcome: 'NO', shares: 600, avgPrice: 65, currentPrice: 72, invested: 390, currentValue: 432, pnl: 42, pnlPercent: 10.8, status: 'open', openedAt: '2026-01-28' },
];

export const transactions: Transaction[] = [
  { id: 't1', type: 'buy', marketSlug: 'btc-100k-by-2026', question: 'Will Bitcoin reach $100,000 by end of 2026?', amount: -310, balanceAfter: 12450.75, status: 'completed', createdAt: '2026-01-10T14:30:00Z' },
  { id: 't2', type: 'deposit', amount: 5000, balanceAfter: 12760.75, status: 'completed', createdAt: '2026-01-08T09:15:00Z' },
  { id: 't3', type: 'buy', marketSlug: 'us-election-2028-democrat', question: 'Will a Democrat win the 2028 US Presidential Election?', amount: -480, balanceAfter: 7760.75, status: 'completed', createdAt: '2026-02-01T11:00:00Z' },
  { id: 't4', type: 'payout', marketSlug: 'sp500-6000-2026', question: 'Will the S&P 500 close above 6,000 in 2026?', amount: 2000, balanceAfter: 8240.75, status: 'completed', createdAt: '2026-03-01T16:45:00Z' },
  { id: 't5', type: 'sell', marketSlug: 'eth-5000-2026', question: 'Will Ethereum surpass $5,000 by end of 2026?', amount: 150, balanceAfter: 6290.75, status: 'completed', createdAt: '2026-02-20T13:20:00Z' },
  { id: 't6', type: 'withdrawal', amount: -2000, balanceAfter: 6140.75, status: 'completed', createdAt: '2026-02-18T10:00:00Z' },
  { id: 't7', type: 'buy', marketSlug: 'gpt6-release-2026', question: 'Will OpenAI release GPT-6 before July 2027?', amount: -280, balanceAfter: 5860.75, status: 'completed', createdAt: '2026-01-20T15:30:00Z' },
  { id: 't8', type: 'fee', amount: -12.50, balanceAfter: 5570.75, status: 'completed', createdAt: '2026-02-25T08:00:00Z' },
];

export const orderBook: { yes: OrderBookEntry[]; no: OrderBookEntry[] } = {
  yes: [
    { price: 67.5, size: 1240, total: 1240 }, { price: 67.0, size: 890, total: 2130 },
    { price: 66.5, size: 2100, total: 4230 }, { price: 66.0, size: 560, total: 4790 },
    { price: 65.5, size: 1800, total: 6590 },
  ],
  no: [
    { price: 33.0, size: 980, total: 980 }, { price: 33.5, size: 1450, total: 2430 },
    { price: 34.0, size: 3200, total: 5630 }, { price: 34.5, size: 750, total: 6380 },
    { price: 35.0, size: 1100, total: 7480 },
  ],
};

export const tradeHistory: TradeHistoryEntry[] = Array.from({ length: 20 }, (_, i) => {
  const sides = ['buy', 'sell'] as const;
  const outcomes = ['YES', 'NO'] as const;
  const time = new Date(); time.setMinutes(time.getMinutes() - i * 3);
  return {
    id: `th${i}`, price: Math.round((64 + Math.random() * 6) * 100) / 100,
    size: Math.floor(50 + Math.random() * 500), outcome: outcomes[Math.floor(Math.random() * 2)],
    time: time.toISOString(), side: sides[Math.floor(Math.random() * 2)],
  };
});

export const leaderboard: LeaderboardEntry[] = [
  { rank: 1, userId: 'u1', name: 'SageTrader', avatarUrl: 'https://images.pexels.com/photos/415829/pexels-photo-415829.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 892400, totalPnl: 412300, totalPnlPercent: 85.7, volume: 2400000, marketsTraded: 156, winRate: 78 },
  { rank: 2, userId: 'u2', name: 'OracleMax', avatarUrl: 'https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 743200, totalPnl: 321000, totalPnlPercent: 75.8, volume: 1980000, marketsTraded: 134, winRate: 74 },
  { rank: 3, userId: 'u3', name: 'NovaPredicts', avatarUrl: 'https://images.pexels.com/photos/1239291/pexels-photo-1239291.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 621000, totalPnl: 289000, totalPnlPercent: 67.2, volume: 1650000, marketsTraded: 198, winRate: 69 },
  { rank: 4, userId: 'u4', name: 'DeltaForce', avatarUrl: 'https://images.pexels.com/photos/697509/pexels-photo-697509.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 534000, totalPnl: 234000, totalPnlPercent: 58.1, volume: 1200000, marketsTraded: 112, winRate: 71 },
  { rank: 5, userId: 'u5', name: 'QuantKing', avatarUrl: 'https://images.pexels.com/photos/1130626/pexels-photo-1130626.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 478000, totalPnl: 198000, totalPnlPercent: 52.3, volume: 980000, marketsTraded: 89, winRate: 66 },
  { rank: 6, userId: 'u6', name: 'AlphaSeeker', avatarUrl: 'https://images.pexels.com/photos/1681010/pexels-photo-1681010.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 412000, totalPnl: 167000, totalPnlPercent: 48.9, volume: 870000, marketsTraded: 76, winRate: 63 },
  { rank: 7, userId: 'u7', name: 'FutureCast', avatarUrl: 'https://images.pexels.com/photos/733872/pexels-photo-733872.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 365000, totalPnl: 143000, totalPnlPercent: 42.1, volume: 720000, marketsTraded: 64, winRate: 61 },
  { rank: 8, userId: 'u8', name: 'ProbMaster', avatarUrl: 'https://images.pexels.com/photos/762020/pexels-photo-762020.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 298000, totalPnl: 112000, totalPnlPercent: 38.5, volume: 590000, marketsTraded: 52, winRate: 58 },
  { rank: 9, userId: 'u9', name: 'ZenTrader', avatarUrl: 'https://images.pexels.com/photos/1300402/pexels-photo-1300402.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 256000, totalPnl: 89000, totalPnlPercent: 29.7, volume: 480000, marketsTraded: 43, winRate: 56 },
  { rank: 10, userId: 'u10', name: 'EdgeFinder', avatarUrl: 'https://images.pexels.com/photos/91227/pexels-photo-91227.jpeg?auto=compress&cs=tinysrgb&w=200', portfolioValue: 198000, totalPnl: 67000, totalPnlPercent: 24.2, volume: 360000, marketsTraded: 38, winRate: 53 },
];

export const aiRecommendations: AIRecommendation[] = [
  { id: 'ai1', marketId: 'm1', marketSlug: 'btc-100k-by-2026', question: 'Will Bitcoin reach $100,000 by end of 2026?', category: 'crypto', outcome: 'YES', confidence: 72, currentPrice: 68, targetPrice: 78, expectedReturn: 14.7, reasoning: 'Historical analysis of Bitcoin post-halving cycles shows strong upward momentum in the 12-18 month window. Current on-chain metrics indicate accumulation by large holders, and institutional ETF inflows remain positive. However, macroeconomic headwinds from potential rate decisions introduce moderate uncertainty.', riskLevel: 'medium', timeframe: '3-6 months', signals: [{ label: 'On-Chain Whales', value: 'Accumulating', positive: true }, { label: 'ETF Inflows', value: '+$42M/week', positive: true }, { label: 'Fear & Greed', value: 'Greed (68)', positive: true }, { label: 'Volatility', value: 'Elevated', positive: false }], createdAt: '2026-03-10T08:00:00Z' },
  { id: 'ai2', marketId: 'm3', marketSlug: 'gpt6-release-2026', question: 'Will OpenAI release GPT-6 before July 2027?', category: 'technology', outcome: 'NO', confidence: 68, currentPrice: 42, targetPrice: 50, expectedReturn: 19.0, reasoning: "OpenAI's historical release cadence between major models averages 18-24 months. GPT-4 launched in March 2023, GPT-5 is expected late 2026, making a GPT-6 release before July 2027 unlikely. Additionally, regulatory scrutiny and safety evaluation timelines further support a longer development cycle.", riskLevel: 'low', timeframe: '12-18 months', signals: [{ label: 'Release Cadence', value: '18-24mo avg', positive: true }, { label: 'Safety Reviews', value: 'Lengthening', positive: true }, { label: 'Compute Needs', value: 'Increasing', positive: true }, { label: 'Competition', value: 'Accelerating', positive: false }], createdAt: '2026-03-09T14:00:00Z' },
  { id: 'ai3', marketId: 'm4', marketSlug: 'us-election-2028-democrat', question: 'Will a Democrat win the 2028 US Presidential Election?', category: 'politics', outcome: 'YES', confidence: 54, currentPrice: 52, targetPrice: 55, expectedReturn: 5.8, reasoning: 'Historical incumbent party performance after two terms shows a slight advantage for the opposition party. Demographic shifts and suburban voting patterns suggest a competitive but lean-Democratic environment. Early polling is limited and should be treated with caution given the 2+ year horizon.', riskLevel: 'high', timeframe: '24+ months', signals: [{ label: 'Historical Pattern', value: 'Opposition edge', positive: true }, { label: 'Demographics', value: 'Shifting blue', positive: true }, { label: 'Incumbency', value: 'Fatigue risk', positive: true }, { label: 'Polling', value: 'Too early', positive: false }], createdAt: '2026-03-08T10:00:00Z' },
];

export const adminMarkets: AdminMarket[] = markets.map((m) => ({
  id: m.id, question: m.question, category: m.category, status: m.status, volume: m.totalVolume, traderCount: m.traderCount, createdAt: '2025-09-15', reported: Math.random() > 0.8,
}));

export const adminUsers: AdminUser[] = [
  { id: 'u1', name: 'SageTrader', email: 'sage@example.com', balance: 892400, volume: 2400000, status: 'active', joinedAt: '2024-01-15', verified: true },
  { id: 'u2', name: 'OracleMax', email: 'oracle@example.com', balance: 743200, volume: 1980000, status: 'active', joinedAt: '2024-02-20', verified: true },
  { id: 'u3', name: 'NovaPredicts', email: 'nova@example.com', balance: 621000, volume: 1650000, status: 'active', joinedAt: '2024-03-10', verified: true },
  { id: 'u4', name: 'DeltaForce', email: 'delta@example.com', balance: 534000, volume: 1200000, status: 'suspended', joinedAt: '2024-04-05', verified: false },
  { id: 'u5', name: 'QuantKing', email: 'quant@example.com', balance: 478000, volume: 980000, status: 'active', joinedAt: '2024-05-12', verified: true },
  { id: 'u6', name: 'AlphaSeeker', email: 'alpha@example.com', balance: 412000, volume: 870000, status: 'active', joinedAt: '2024-06-18', verified: true },
  { id: 'u7', name: 'SuspiciousUser', email: 'sus@example.com', balance: 50000, volume: 120000, status: 'banned', joinedAt: '2024-08-01', verified: false },
];

export const portfolioChartData = [
  { t: 'Jan 1', value: 18000 }, { t: 'Jan 15', value: 19500 }, { t: 'Feb 1', value: 21000 },
  { t: 'Feb 15', value: 22800 }, { t: 'Mar 1', value: 24600 }, { t: 'Mar 15', value: 26200 },
  { t: 'Apr 1', value: 27800 }, { t: 'Apr 15', value: 28934 },
];

export const pnlBreakdownData = [
  { name: 'Crypto', value: 1450, color: 'hsl(38 92% 55%)' },
  { name: 'Politics', value: 980, color: 'hsl(166 72% 45%)' },
  { name: 'Tech', value: 620, color: 'hsl(200 85% 55%)' },
  { name: 'Sports', value: -120, color: 'hsl(0 72% 51%)' },
  { name: 'Economy', value: 490, color: 'hsl(280 60% 65%)' },
];

export const tradingVolumeData = [
  { t: 'Mon', volume: 240000 }, { t: 'Tue', volume: 310000 }, { t: 'Wed', volume: 280000 },
  { t: 'Thu', volume: 420000 }, { t: 'Fri', volume: 510000 }, { t: 'Sat', volume: 380000 },
  { t: 'Sun', volume: 290000 },
];

export const platformStats = { totalVolume: 89400000, totalTraders: 128400, activeMarkets: 342, totalPayouts: 23400000 };

export function getMarketBySlug(slug: string): Market | undefined { return markets.find((m) => m.slug === slug); }
export function getFeaturedMarkets(): Market[] { return markets.filter((m) => m.featured); }
export function getMarketsByCategory(category: string): Market[] { return category === 'all' ? markets : markets.filter((m) => m.category === category); }
export function searchMarkets(query: string): Market[] {
  const q = query.toLowerCase();
  return markets.filter((m) => m.question.toLowerCase().includes(q) || m.tags.some((t) => t.toLowerCase().includes(q)) || m.category.toLowerCase().includes(q));
}
export function getRecommendationByMarket(marketSlug: string): AIRecommendation | undefined { return aiRecommendations.find((r) => r.marketSlug === marketSlug); }
