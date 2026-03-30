import React from "react";
import { Boxes, AlertTriangle, PackageX, TrendingDown, Layers } from "lucide-react";

export interface InventoryAnalyticsResponse {
  report_type: string;
  generated_at: string;
  summary: {
    total_products: number;
    total_stock_value: number;
    low_stock_count: number;
    out_of_stock_count: number;
  };
  items: {
    product_id: string;
    product_name: string;
    category: string;
    current_stock: number;
    reorder_level: number;
    stock_value: number;
    status: string;
  }[];
  low_stock_items: {
    product_id: string;
    product_name: string;
    category: string;
    current_stock: number;
    reorder_level: number;
    stock_value: number;
    status: string;
  }[];
  category_summary: {
    category: string;
    total_products: number;
    total_stock_value: number;
    low_stock_count: number;
  }[];
  insights: {
    critical_products: string[];
    highest_value_category?: string;
    stock_health: string;
    recommendation: string;
  };
  natural_language_summary: string;
}

export const InventoryAnalyticsComponent = ({ data }: { data: InventoryAnalyticsResponse }) => {
  const isHealthy = data.insights.stock_health === "healthy";
  const hasIssues = data.summary.low_stock_count > 0 || data.summary.out_of_stock_count > 0;

  return (
    <div className="w-full flex justify-end">
      <div className="bg-card w-full max-w-2xl rounded-2xl border border-border/50 shadow-sm overflow-hidden flex flex-col items-start gap-4 p-5 animate-fade-in my-2">
        <div className="flex items-center gap-2 text-orange-500 mb-2">
          <Boxes className="w-5 h-5" />
          <h3 className="font-semibold text-lg bg-clip-text text-transparent bg-gradient-to-r from-orange-400 to-amber-500">Inventory Status</h3>
        </div>

        <p className="text-sm text-muted-foreground leading-relaxed">{data.natural_language_summary}</p>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 w-full mt-2">
          <div className="bg-card border border-border/50 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground flex items-center gap-1">
              <Layers className="w-3 h-3" /> Total Items
            </span>
            <span className="text-lg font-bold">{data.summary.total_products}</span>
          </div>
          <div className="bg-card border border-border/50 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-muted-foreground">Value</span>
            <span className="text-lg font-bold text-orange-500">${data.summary.total_stock_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
          </div>
          <div className="bg-amber-500/10 border border-amber-500/20 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-amber-600 dark:text-amber-500 flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> Low Stock
            </span>
            <span className="text-lg font-bold text-amber-600 dark:text-amber-500">{data.summary.low_stock_count}</span>
          </div>
          <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-3 flex flex-col gap-1">
            <span className="text-xs text-red-600 dark:text-red-500 flex items-center gap-1">
              <PackageX className="w-3 h-3" /> Out of Stock
            </span>
            <span className="text-lg font-bold text-red-600 dark:text-red-500">{data.summary.out_of_stock_count}</span>
          </div>
        </div>

        {hasIssues && data.low_stock_items && data.low_stock_items.length > 0 && (
          <div className="w-full mt-3 border border-border/50 rounded-xl overflow-hidden">
            <div className="bg-muted/40 px-4 py-2 border-b border-border/50 text-xs font-semibold flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Action Required: Low/Out of Stock
            </div>
            <div className="max-h-[200px] overflow-y-auto w-full">
              <table className="w-full text-sm text-left">
                <thead className="bg-muted/20 text-xs uppercase text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2 font-medium">Product</th>
                    <th className="px-4 py-2 font-medium text-right">Stock</th>
                    <th className="px-4 py-2 font-medium text-center">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50">
                  {data.low_stock_items.slice(0, 5).map((item, idx) => (
                    <tr key={idx} className="hover:bg-muted/30">
                      <td className="px-4 py-2">
                        <p className="font-medium text-foreground truncate max-w-[150px]" title={item.product_name}>
                          {item.product_name}
                        </p>
                        <p className="text-[10px] text-muted-foreground">{item.category}</p>
                      </td>
                      <td className="px-4 py-2 text-right">
                        <span className="font-semibold">{item.current_stock}</span> <span className="text-xs text-muted-foreground">/ {item.reorder_level}</span>
                      </td>
                      <td className="px-4 py-2 text-center">
                        <span
                          className={`text-[10px] uppercase px-2 py-0.5 rounded-full font-semibold ${item.status === "OUT_OF_STOCK" ? "bg-red-500/10 text-red-500 border border-red-500/20" : "bg-amber-500/10 text-amber-500 border border-amber-500/20"}`}
                        >
                          {item.status.replace("_", " ")}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
