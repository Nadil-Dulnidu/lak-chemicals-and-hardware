import React from "react";
import { LineChart, Star, Package, Layers, Info } from "lucide-react";

export interface ProductPerformanceResponse {
  report_type: string;
  start_date: string;
  end_date: string;
  summary: {
    total_revenue: number;
    total_quantity_sold: number;
    top_product_count: number;
    date_range_days: number;
  };
  top_products: {
    product_id: string;
    product_name: string;
    category: string;
    total_quantity_sold: number;
    total_revenue: number;
    number_of_orders: number;
    average_order_quantity: number;
  }[];
  category_performance: {
    category: string;
    total_quantity: number;
    total_revenue: number;
    unique_products: number;
  }[];
  insights: {
    top_product?: string;
    top_category?: string;
    highest_demand_product?: string;
    performance_trend: string;
    recommendation: string;
  };
  natural_language_summary: string;
}

export const ProductPerformanceComponent = ({ data }: { data: ProductPerformanceResponse }) => {
  return (
    <div className="w-full flex justify-end">
      <div className="bg-card w-full max-w-2xl rounded-2xl border border-border/50 shadow-sm overflow-hidden flex flex-col items-start gap-4 p-5 animate-fade-in my-2">
        <div className="flex items-center gap-2 text-orange-500 mb-2">
          <LineChart className="w-5 h-5" />
          <h3 className="font-semibold text-lg bg-clip-text text-transparent bg-gradient-to-r from-orange-400 to-amber-500">Product Performance</h3>
        </div>

        <p className="text-sm text-muted-foreground leading-relaxed">{data.natural_language_summary}</p>

        <div className="w-full space-y-4">
          <h4 className="text-sm font-semibold flex items-center gap-2 border-b border-border/50 pb-2">
            <Star className="w-4 h-4 text-amber-400" />
            Top Performing Products
          </h4>
          <div className="grid grid-cols-1 gap-2">
            {data.top_products.slice(0, 3).map((product, idx) => (
              <div key={idx} className="bg-card border border-border/60 rounded-xl p-3 flex justify-between items-center transition-all hover:bg-muted/30">
                <div className="flex items-center gap-3 overflow-hidden">
                  <div className="w-8 h-8 rounded-full bg-orange-500/10 flex items-center justify-center text-orange-500 font-bold text-xs shrink-0">#{idx + 1}</div>
                  <div className="overflow-hidden">
                    <p className="text-sm font-semibold truncate">{product.product_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{product.category}</p>
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-sm font-bold text-emerald-500">${product.total_revenue.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
                  <p className="text-xs text-muted-foreground">{product.total_quantity_sold.toLocaleString()} sold</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-4 w-full mt-2">
          <h4 className="text-xs font-semibold text-amber-600 mb-2 uppercase tracking-wider flex items-center gap-1">
            <Info className="w-3.5 h-3.5" /> Recommendation
          </h4>
          <p className="text-sm text-amber-700 dark:text-amber-400">{data.insights.recommendation}</p>
        </div>
      </div>
    </div>
  );
};
