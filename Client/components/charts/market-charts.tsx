'use client';

import * as React from 'react';
import {
  Area,
  AreaChart as RAreaChart,
  Bar,
  BarChart as RBarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart as RLineChart,
  Pie,
  PieChart as RPieChart,
  RadialBar,
  RadialBarChart as RRadialBarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  ReferenceLine,
  ComposedChart,
  type TooltipProps,
} from 'recharts';
import { cn } from '@/lib/utils';
import { Card } from '@/components/ui/card';
import { AIRecommendationCard } from '@/components/ai/recommendation-card';
import { aiRecommendations } from '@/lib/mock-data';
import type { AIRecommendation } from '@/lib/types';
import { Brain } from 'lucide-react';

// ============================================================
// Shared Chart Tooltip
// ============================================================
function ChartTooltip({
  active,
  payload,
  label,
  formatter,
}: TooltipProps<number, string> & { formatter?: (v: number) => string }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 shadow-lg">
      {label && <p className="mb-1 text-xs font-medium text-muted-foreground">{label}</p>}
      {payload.map((entry, i) => (
        <div key={i} className="flex items-center gap-2 text-sm">
          <span className="h-2 w-2 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-medium tabular-nums">
            {formatter ? formatter(Number(entry.value)) : entry.value}
          </span>
        </div>
      ))}
    </div>
  );
}

const axisStyle = { fontSize: '11px', fill: 'hsl(var(--muted-foreground))' };

// ============================================================
// AreaChart
// ============================================================
interface AreaChartProps {
  data: Record<string, number | string>[];
  xKey: string;
  areas: { key: string; color: string; name?: string }[];
  className?: string;
  height?: number;
  yFormatter?: (v: number) => string;
  showGrid?: boolean;
}

export function AreaChart({
  data,
  xKey,
  areas,
  className,
  height = 260,
  yFormatter,
  showGrid = true,
}: AreaChartProps) {
  return (
    <ResponsiveContainer className={className} width="100%" height={height}>
      <RAreaChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
        <defs>
          {areas.map((a) => (
            <linearGradient key={a.key} id={`area-${a.key}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={a.color} stopOpacity={0.3} />
              <stop offset="100%" stopColor={a.color} stopOpacity={0} />
            </linearGradient>
          ))}
        </defs>
        {showGrid && (
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
        )}
        <XAxis dataKey={xKey} tick={axisStyle} tickLine={false} axisLine={false} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} />
        <Tooltip content={<ChartTooltip formatter={yFormatter} />} />
        {areas.map((a) => (
          <Area
            key={a.key}
            type="monotone"
            dataKey={a.key}
            name={a.name ?? a.key}
            stroke={a.color}
            strokeWidth={2}
            fill={`url(#area-${a.key})`}
            animationDuration={600}
          />
        ))}
      </RAreaChart>
    </ResponsiveContainer>
  );
}

// ============================================================
// LineChart
// ============================================================
interface LineChartProps {
  data: Record<string, number | string>[];
  xKey: string;
  lines: { key: string; color: string; name?: string; dashed?: boolean }[];
  className?: string;
  height?: number;
  yFormatter?: (v: number) => string;
  showGrid?: boolean;
  referenceLine?: { y: number; label: string };
}

export function LineChart({
  data,
  xKey,
  lines,
  className,
  height = 260,
  yFormatter,
  showGrid = true,
  referenceLine,
}: LineChartProps) {
  return (
    <ResponsiveContainer className={className} width="100%" height={height}>
      <RLineChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
        {showGrid && (
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
        )}
        <XAxis dataKey={xKey} tick={axisStyle} tickLine={false} axisLine={false} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={40} domain={[0, 100]} />
        <Tooltip content={<ChartTooltip formatter={yFormatter} />} />
        {referenceLine && (
          <ReferenceLine
            y={referenceLine.y}
            stroke="hsl(var(--muted-foreground))"
            strokeDasharray="4 4"
            label={{
              value: referenceLine.label,
              fontSize: 10,
              fill: 'hsl(var(--muted-foreground))',
            }}
          />
        )}
        {lines.map((l) => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            name={l.name ?? l.key}
            stroke={l.color}
            strokeWidth={2}
            strokeDasharray={l.dashed ? '5 5' : undefined}
            dot={false}
            activeDot={{ r: 4 }}
            animationDuration={600}
          />
        ))}
      </RLineChart>
    </ResponsiveContainer>
  );
}

// ============================================================
// BarChart
// ============================================================
interface BarChartProps {
  data: Record<string, number | string>[];
  xKey: string;
  bars: { key: string; color: string; name?: string }[];
  className?: string;
  height?: number;
  yFormatter?: (v: number) => string;
  showGrid?: boolean;
}

export function BarChart({
  data,
  xKey,
  bars,
  className,
  height = 260,
  yFormatter,
  showGrid = true,
}: BarChartProps) {
  return (
    <ResponsiveContainer className={className} width="100%" height={height}>
      <RBarChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
        {showGrid && (
          <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
        )}
        <XAxis dataKey={xKey} tick={axisStyle} tickLine={false} axisLine={false} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={50} />
        <Tooltip
          content={<ChartTooltip formatter={yFormatter} />}
          cursor={{ fill: 'hsl(var(--muted) / 0.5)' }}
        />
        {bars.map((b) => (
          <Bar
            key={b.key}
            dataKey={b.key}
            name={b.name ?? b.key}
            fill={b.color}
            radius={[4, 4, 0, 0]}
            animationDuration={600}
            barSize={28}
          >
            <Cell fill={b.color} />
          </Bar>
        ))}
      </RBarChart>
    </ResponsiveContainer>
  );
}

// ============================================================
// DonutChart
// ============================================================
interface DonutChartProps {
  data: { name: string; value: number; color: string }[];
  className?: string;
  height?: number;
  innerRadius?: number;
  outerRadius?: number;
  formatter?: (v: number) => string;
}

export function DonutChart({
  data,
  className,
  height = 260,
  innerRadius = 55,
  outerRadius = 85,
  formatter,
}: DonutChartProps) {
  return (
    <ResponsiveContainer className={className} width="100%" height={height}>
      <RPieChart>
        <Pie
          data={data}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius={outerRadius}
          paddingAngle={3}
          animationDuration={600}
        >
          {data.map((entry, i) => (
            <Cell key={i} fill={entry.color} stroke="hsl(var(--card))" strokeWidth={2} />
          ))}
        </Pie>
        <Tooltip content={<ChartTooltip formatter={formatter} />} />
      </RPieChart>
    </ResponsiveContainer>
  );
}

// ============================================================
// GaugeChart
// ============================================================
interface GaugeChartProps {
  value: number;
  label?: string;
  className?: string;
  height?: number;
  color?: string;
}

export function GaugeChart({
  value,
  className,
  height = 200,
  color = 'hsl(var(--primary))',
}: GaugeChartProps) {
  const data = [{ name: 'gauge', value, fill: color }];
  return (
    <ResponsiveContainer className={className} width="100%" height={height}>
      <RRadialBarChart
        cx="50%"
        cy="50%"
        innerRadius="70%"
        outerRadius="100%"
        data={data}
        startAngle={90}
        endAngle={-270}
      >
        <RadialBar
          dataKey="value"
          cornerRadius={10}
          background={{ fill: 'hsl(var(--muted))' }}
          animationDuration={800}
        />
      </RRadialBarChart>
    </ResponsiveContainer>
  );
}

// ============================================================
// ComposedChartComponent
// ============================================================
interface ComposedChartProps {
  data: Record<string, number | string>[];
  xKey: string;
  bars: { key: string; color: string; name?: string }[];
  lines: { key: string; color: string; name?: string }[];
  className?: string;
  height?: number;
  yFormatter?: (v: number) => string;
}

export function ComposedChartComponent({
  data,
  xKey,
  bars,
  lines,
  className,
  height = 260,
  yFormatter,
}: ComposedChartProps) {
  return (
    <ResponsiveContainer className={className} width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 10, right: 8, left: 0, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
        <XAxis dataKey={xKey} tick={axisStyle} tickLine={false} axisLine={false} />
        <YAxis tick={axisStyle} tickLine={false} axisLine={false} width={50} />
        <Tooltip
          content={<ChartTooltip formatter={yFormatter} />}
          cursor={{ fill: 'hsl(var(--muted) / 0.5)' }}
        />
        {bars.map((b) => (
          <Bar
            key={b.key}
            dataKey={b.key}
            name={b.name ?? b.key}
            fill={b.color}
            radius={[4, 4, 0, 0]}
            animationDuration={600}
            barSize={28}
          />
        ))}
        {lines.map((l) => (
          <Line
            key={l.key}
            type="monotone"
            dataKey={l.key}
            name={l.name ?? l.key}
            stroke={l.color}
            strokeWidth={2}
            dot={false}
            animationDuration={600}
          />
        ))}
      </ComposedChart>
    </ResponsiveContainer>
  );
}

// ============================================================
// AIRecommendationList Component
// ============================================================
interface AIRecommendationListProps {
  recommendations?: AIRecommendation[];
  className?: string;
  compact?: boolean;
}

export function AIRecommendationList({
  recommendations = aiRecommendations,
  className,
  compact,
}: AIRecommendationListProps) {
  return (
    <div className={cn('grid gap-4 sm:grid-cols-2 lg:grid-cols-3', className)}>
      {recommendations.map((rec) => (
        <AIRecommendationCard key={rec.id} recommendation={rec} compact={compact} />
      ))}
    </div>
  );
}

// ============================================================
// AIInsightBanner Component
// ============================================================
interface AIInsightBannerProps {
  className?: string;
}

export function AIInsightBanner({ className }: AIInsightBannerProps) {
  return (
    <Card className={cn('relative overflow-hidden p-6', className)}>
      <div className="absolute inset-0 bg-gradient-to-r from-primary/10 via-transparent to-chart-2/10" />
      <div className="relative flex items-center gap-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary to-chart-2 text-primary-foreground">
          <Brain className="h-7 w-7" />
        </div>
        <div className="flex-1">
          <h2 className="font-display text-lg font-bold">AI-Powered Predictions</h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Get data-driven market recommendations powered by advanced models analyzing on-chain
            data, sentiment, and historical patterns.
          </p>
        </div>
      </div>
    </Card>
  );
}

// ============================================================
// Barrel re-exports
// ============================================================
export { AIRecommendationCard } from '@/components/ai/recommendation-card';