import React from "react";
import { BarChart3, TrendingUp, ShoppingCart, DollarSign, Calendar } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export interface SalesAnalyticsResponse {
  report_type: string;
  start_date: string;
  end_date: string;
  summary: {
    total_sales: number;
    total_revenue: number;
    total_quantity: number;
    average_sale_value: number;
  };
  trend: {
    period: string;
    total_sales: number;
    total_revenue: number;
    total_quantity: number;
  }[];
  product_breakdown: {
    product_id: string;
    product_name: string;
    quantity_sold: number;
    revenue: number;
    sales_count: number;
  }[];
  category_breakdown: {
    category: string;
    quantity_sold: number;
    revenue: number;
    sales_count: number;
  }[];
  insights: {
    top_product?: string;
    top_category?: string;
    highest_revenue_period?: string;
    revenue_trend: string;
  };
  query_parameters: unknown;
  natural_language_summary: string;
}

export const SalesAnalyticsComponent = ({ data }: { data: SalesAnalyticsResponse }) => {
  return (
    <div className="w-full flex justify-end">
      <div className="bg-card w-full max-w-2xl rounded-2xl border border-border/50 shadow-sm overflow-hidden flex flex-col items-start gap-4 p-5 animate-fade-in my-2">
        <div className="flex items-center gap-2 text-orange-500 mb-2">
          <BarChart3 className="w-5 h-5" />
          <h3 className="font-semibold text-lg bg-clip-text text-transparent bg-gradient-to-r from-orange-400 to-amber-500">Sales Analytics overview</h3>
        </div>

        <p className="text-sm text-muted-foreground leading-relaxed">{data.natural_language_summary}</p>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 w-full mt-2">
          <div className="bg-card border border-border/50 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <DollarSign className="w-3 h-3" /> Total Revenue
            </span>
            <span className="text-lg font-bold text-orange-500">${data.summary.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
          <div className="bg-card border border-border/50 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <ShoppingCart className="w-3 h-3" /> Total Sales
            </span>
            <span className="text-lg font-bold">{data.summary.total_sales.toLocaleString()}</span>
          </div>
          <div className="bg-card border border-border/50 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <TrendingUp className="w-3 h-3" /> Avg. Order
            </span>
            <span className="text-lg font-bold">${data.summary.average_sale_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
          <div className="bg-card border border-border/50 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Trend</span>
            <span className="text-lg font-bold capitalize truncate">{data.insights.revenue_trend}</span>
          </div>
        </div>

        {data.trend && data.trend.length > 0 && (
          <div className="w-full h-48 mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.trend} margin={{ top: 5, right: 0, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#333" opacity={0.2} />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
                <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} tickFormatter={(val) => `$${val}`} />
                <Tooltip
                  cursor={{ fill: "rgba(249, 115, 22, 0.1)" }}
                  contentStyle={{ backgroundColor: "hsl(var(--card))", borderRadius: "8px", border: "1px solid hsl(var(--border))" }}
                  itemStyle={{ color: "#f97316", fontWeight: "bold" }}
                />
                <Bar dataKey="total_revenue" name="Revenue" fill="#f97316" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="w-full bg-orange-500/5 rounded-xl border border-orange-500/10 p-3 flex flex-col sm:flex-row gap-4 justify-between mt-2">
          <div>
            <p className="text-xs text-muted-foreground mb-1">Top Category</p>
            <p className="font-semibold text-sm">{data.insights.top_category || "N/A"}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground mb-1">Top Product</p>
            <p className="font-semibold text-sm truncate max-w-[200px]" title={data.insights.top_product}>
              {data.insights.top_product || "N/A"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 mt-1 w-full pt-3 border-t border-border/50 text-xs text-muted-foreground">
          <Calendar className="w-3.5 h-3.5" />
          <span>
            Period: {new Date(data.start_date).toLocaleDateString()} to {new Date(data.end_date).toLocaleDateString()}
          </span>
        </div>
      </div>
    </div>
  );
};
