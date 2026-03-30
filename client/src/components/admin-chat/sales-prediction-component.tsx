import React from "react";
import { TrendingUp, BarChart3, AlertTriangle, Calendar, CheckCircle2, TrendingDown } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export interface SalesPredictionResponse {
  report_type: string;
  historical_start_date: string;
  historical_end_date: string;
  prediction_start_date: string;
  prediction_end_date: string;
  historical_summary: {
    total_sales: number;
    total_revenue: number;
    total_quantity: number;
    average_sale_value: number;
  };
  forecast: {
    period: string;
    predicted_sales: number;
    predicted_revenue: number;
    predicted_quantity: number;
  }[];
  insights: {
    expected_growth_rate: number;
    predicted_top_product?: string;
    predicted_top_category?: string;
    demand_trend: string;
    risk_level: string;
  };
  natural_language_summary: string;
}

export const SalesPredictionComponent = ({ data }: { data: SalesPredictionResponse }) => {
  const isPositiveGrowth = data.insights.expected_growth_rate >= 0;

  return (
    <div className="w-full flex justify-end">
      <div className="bg-card w-full max-w-2xl rounded-2xl border border-border/50 shadow-sm overflow-hidden flex flex-col items-start gap-4 p-5 animate-fade-in my-2">
        <div className="flex items-center gap-2 text-orange-500 mb-2">
          <TrendingUp className="w-5 h-5" />
          <h3 className="font-semibold text-lg bg-clip-text text-transparent bg-gradient-to-r from-orange-400 to-amber-500">Sales Prediction & Forecast</h3>
        </div>

        <p className="text-sm text-muted-foreground leading-relaxed">{data.natural_language_summary}</p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 w-full mt-2">
          <div className="bg-orange-500/5 border border-orange-500/10 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Expected Growth</span>
            <div className={`text-lg font-bold flex items-center gap-1 ${isPositiveGrowth ? "text-emerald-500" : "text-red-500"}`}>
              {isPositiveGrowth ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {Math.abs(data.insights.expected_growth_rate).toFixed(1)}%
            </div>
          </div>
          <div className="bg-card border border-border/50 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Demand Trend</span>
            <span className="text-lg font-bold capitalize">{data.insights.demand_trend}</span>
          </div>
          <div className="bg-card border border-border/50 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Top Product</span>
            <span className="text-sm font-bold truncate" title={data.insights.predicted_top_product}>
              {data.insights.predicted_top_product || "N/A"}
            </span>
          </div>
          <div className="bg-card border border-border/50 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Risk Level</span>
            <span className="text-lg font-bold capitalize">{data.insights.risk_level}</span>
          </div>
        </div>

        {data.forecast && data.forecast.length > 0 && (
          <div className="w-full h-48 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data.forecast} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorRevenue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f97316" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#f97316" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" opacity={0.2} />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                <Tooltip contentStyle={{ backgroundColor: "hsl(var(--card))", borderRadius: "8px", border: "1px solid hsl(var(--border))" }} itemStyle={{ color: "#f97316", fontWeight: "bold" }} />
                <Area type="monotone" dataKey="predicted_revenue" name="Expected Revenue" stroke="#f97316" strokeWidth={2} fillOpacity={1} fill="url(#colorRevenue)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="flex items-center gap-2 mt-2 w-full pt-3 border-t border-border/50 text-xs text-muted-foreground">
          <Calendar className="w-3.5 h-3.5" />
          <span>
            Forecast Period: {new Date(data.prediction_start_date).toLocaleDateString()} to {new Date(data.prediction_end_date).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
};
