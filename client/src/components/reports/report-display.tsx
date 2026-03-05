"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { DollarSign, ShoppingBag, TrendingUp, Package, AlertTriangle, BarChart3, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";
import { SalesReportData, InventoryReportData, ReportType } from "@/lib/types";

// ============= Type Definitions =============
interface ProductPerformanceData {
  report_type: string;
  start_date: string;
  end_date: string;
  top_products?: {
    product_id: string;
    product_name: string;
    category?: string;
    total_quantity_sold: number;
    total_revenue: number | string;
    number_of_orders: number;
    average_order_quantity?: number | string;
  }[];
  summary?: {
    top_product_count: number;
    total_revenue: number;
    total_quantity_sold: number;
    date_range_days?: number;
  };
  category_performance?: {
    category: string;
    total_quantity: number;
    total_revenue: number;
    unique_products: number;
  }[];
}

interface LowStockData {
  report_type: string;
  generated_at: string;
  threshold_percentage: number;
  summary: {
    total_low_stock_products: number;
    out_of_stock_count: number;
    critical_count: number;
    total_recommended_order_quantity: number;
  };
  items: {
    product_id: string;
    product_name: string;
    category?: string;
    current_stock: number;
    reorder_level: number;
    stock_percentage: number;
    recommended_order_quantity: number;
  }[];
}

// ============= Sales Report Display =============
export function SalesReportDisplay({ data }: { data: SalesReportData }) {
  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/20">
                <DollarSign className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Revenue</p>
                <p className="text-xl font-bold text-green-400">LKR {data.summary.total_revenue?.toLocaleString() || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <ShoppingBag className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Sales</p>
                <p className="text-xl font-bold text-blue-400">{data.summary.total_sales || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Package className="h-5 w-5 text-purple-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Items Sold</p>
                <p className="text-xl font-bold text-purple-400">{data.summary.total_quantity || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-orange-500/10 to-orange-600/5 border-orange-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-500/20">
                <TrendingUp className="h-5 w-5 text-orange-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Avg Sale Value</p>
                <p className="text-xl font-bold text-orange-400">LKR {data.summary.average_sale_value?.toLocaleString() || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Date Range */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Calendar className="h-4 w-4" />
        <span>
          {new Date(data.start_date).toLocaleDateString()} - {new Date(data.end_date).toLocaleDateString()}
        </span>
      </div>

      {/* Sales by Period */}
      {data.items && data.items.length > 0 && (
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-orange-400" />
              Sales by Period
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left p-3 font-medium text-muted-foreground">Period</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Sales</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Quantity</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Revenue</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item, idx) => (
                    <tr key={idx} className="border-b border-border/30 hover:bg-muted/30">
                      <td className="p-3 font-medium">{item.period}</td>
                      <td className="p-3 text-right">{item.total_sales}</td>
                      <td className="p-3 text-right">{item.total_quantity}</td>
                      <td className="p-3 text-right text-green-400">LKR {item.total_revenue?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Product Breakdown */}
      {data.product_breakdown && data.product_breakdown.length > 0 && (
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Package className="h-4 w-4 text-blue-400" />
              Top Products
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.product_breakdown.slice(0, 10).map((product, idx) => (
                <div key={product.product_id} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-bold text-muted-foreground w-6">#{idx + 1}</span>
                    <div>
                      <p className="font-medium">{product.product_name}</p>
                      <p className="text-xs text-muted-foreground">
                        {product.quantity_sold} units · {product.sales_count} orders
                      </p>
                    </div>
                  </div>
                  <span className="font-bold text-green-400">LKR {product.revenue?.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Breakdown */}
      {data.category_breakdown && data.category_breakdown.length > 0 && (
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-purple-400" />
              Sales by Category
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.category_breakdown.map((cat) => (
                <div key={cat.category} className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
                  <div>
                    <p className="font-medium capitalize">{cat.category?.replace("_", " ")}</p>
                    <p className="text-xs text-muted-foreground">
                      {cat.quantity_sold} units · {cat.sales_count} orders
                    </p>
                  </div>
                  <span className="font-bold text-green-400">LKR {cat.revenue?.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============= Inventory Report Display =============
export function InventoryReportDisplay({ data }: { data: InventoryReportData }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "OK":
        return "bg-green-500/10 text-green-400 border-green-500/30";
      case "LOW":
        return "bg-yellow-500/10 text-yellow-400 border-yellow-500/30";
      case "OUT_OF_STOCK":
        return "bg-red-500/10 text-red-400 border-red-500/30";
      default:
        return "bg-gray-500/10 text-gray-400 border-gray-500/30";
    }
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Package className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Products</p>
                <p className="text-xl font-bold text-blue-400">{data.summary.total_products}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/20">
                <DollarSign className="h-5 w-5 text-green-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Stock Value</p>
                <p className="text-xl font-bold text-green-400">LKR {data.summary.total_stock_value?.toLocaleString()}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border-yellow-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-yellow-500/20">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Low Stock</p>
                <p className="text-xl font-bold text-yellow-400">{data.summary.low_stock_count}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/20">
                <Package className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Out of Stock</p>
                <p className="text-xl font-bold text-red-400">{data.summary.out_of_stock_count}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Generated At */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Calendar className="h-4 w-4" />
        <span>Generated: {new Date(data.generated_at).toLocaleString()}</span>
      </div>

      {/* Low Stock Items */}
      {data.low_stock_items && data.low_stock_items.length > 0 && (
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-400" />
              Low Stock Items ({data.low_stock_items.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left p-3 font-medium text-muted-foreground">Product</th>
                    <th className="text-left p-3 font-medium text-muted-foreground">Category</th>
                    <th className="text-center p-3 font-medium text-muted-foreground">Status</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Current</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Reorder Level</th>
                  </tr>
                </thead>
                <tbody>
                  {data.low_stock_items.map((item) => (
                    <tr key={item.product_id} className="border-b border-border/30 hover:bg-muted/30">
                      <td className="p-3 font-medium">{item.product_name}</td>
                      <td className="p-3 text-muted-foreground capitalize">{item.category?.replace("_", " ")}</td>
                      <td className="p-3 text-center">
                        <Badge className={cn("border", getStatusColor(item.status))}>{item.status.replace("_", " ")}</Badge>
                      </td>
                      <td className={cn("p-3 text-right font-medium", item.current_stock === 0 ? "text-red-400" : "text-yellow-400")}>{item.current_stock}</td>
                      <td className="p-3 text-right text-muted-foreground">{item.reorder_level}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* All Items */}
      {data.items && data.items.length > 0 && (
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <Package className="h-4 w-4 text-blue-400" />
              All Products ({data.items.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto max-h-[400px]">
              <table className="w-full text-sm">
                <thead className="sticky top-0 bg-background">
                  <tr className="border-b border-border/50">
                    <th className="text-left p-3 font-medium text-muted-foreground">Product</th>
                    <th className="text-left p-3 font-medium text-muted-foreground">Category</th>
                    <th className="text-center p-3 font-medium text-muted-foreground">Status</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Stock</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Value</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => (
                    <tr key={item.product_id} className="border-b border-border/30 hover:bg-muted/30">
                      <td className="p-3 font-medium">{item.product_name}</td>
                      <td className="p-3 text-muted-foreground capitalize">{item.category?.replace("_", " ")}</td>
                      <td className="p-3 text-center">
                        <Badge className={cn("border", getStatusColor(item.status))}>{item.status.replace("_", " ")}</Badge>
                      </td>
                      <td className="p-3 text-right">{item.current_stock}</td>
                      <td className="p-3 text-right text-green-400">LKR {item.stock_value?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============= Product Performance Report Display =============
export function ProductPerformanceDisplay({ data }: { data: ProductPerformanceData }) {
  return (
    <div className="space-y-6">
      {/* Date Range */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Calendar className="h-4 w-4" />
        <span>
          {new Date(data.start_date).toLocaleDateString()} - {new Date(data.end_date).toLocaleDateString()}
        </span>
        {data.summary?.date_range_days && (
          <>
            <span className="text-muted-foreground/50">·</span>
            <span>{data.summary.date_range_days} days</span>
          </>
        )}
      </div>

      {/* Summary */}
      {data.summary && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card className="bg-gradient-to-br from-purple-500/10 to-purple-600/5 border-purple-500/20">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/20">
                  <Package className="h-5 w-5 text-purple-400" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Products Analyzed</p>
                  <p className="text-xl font-bold text-purple-400">{data.summary.top_product_count}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-green-500/10 to-green-600/5 border-green-500/20">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-500/20">
                  <DollarSign className="h-5 w-5 text-green-400" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Total Revenue</p>
                  <p className="text-xl font-bold text-green-400">LKR {data.summary.total_revenue?.toLocaleString()}</p>
                </div>
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
            <CardContent className="p-4">
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-blue-500/20">
                  <ShoppingBag className="h-5 w-5 text-blue-400" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Total Quantity Sold</p>
                  <p className="text-xl font-bold text-blue-400">{data.summary.total_quantity_sold}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Top Products */}
      {data.top_products && data.top_products.length > 0 && (
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-orange-400" />
              Top Performing Products
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {data.top_products.map((product, idx) => (
                <div key={product.product_id} className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center gap-4">
                    <div
                      className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center font-bold text-lg",
                        idx === 0 ? "bg-yellow-500/20 text-yellow-400" : idx === 1 ? "bg-gray-400/20 text-gray-400" : idx === 2 ? "bg-orange-600/20 text-orange-600" : "bg-muted text-muted-foreground",
                      )}
                    >
                      {idx + 1}
                    </div>
                    <div>
                      <p className="font-medium">{product.product_name}</p>
                      <p className="text-xs text-muted-foreground capitalize">
                        {product.category?.replace("_", " ")} · {product.number_of_orders} orders · avg {product.average_order_quantity} per order
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-green-400">LKR {Number(product.total_revenue)?.toLocaleString()}</p>
                    <p className="text-xs text-muted-foreground">{product.total_quantity_sold} units</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Category Performance */}
      {data.category_performance && data.category_performance.length > 0 && (
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-purple-400" />
              Category Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {data.category_performance.map((cat) => (
                <div key={cat.category} className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                  <div>
                    <p className="font-medium capitalize">{cat.category?.replace("_", " ")}</p>
                    <p className="text-xs text-muted-foreground">
                      {cat.total_quantity} units · {cat.unique_products} product{cat.unique_products !== 1 ? "s" : ""}
                    </p>
                  </div>
                  <span className="font-bold text-green-400">LKR {cat.total_revenue?.toLocaleString()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============= Low Stock Report Display =============
export function LowStockReportDisplay({ data }: { data: LowStockData }) {
  const getPriorityFromPercentage = (pct: number) => {
    if (pct === 0) return { label: "Out of Stock", color: "bg-red-500/10 text-red-400 border-red-500/30" };
    if (pct <= 10) return { label: "Critical", color: "bg-red-500/10 text-red-400 border-red-500/30" };
    if (pct <= 30) return { label: "High", color: "bg-orange-500/10 text-orange-400 border-orange-500/30" };
    if (pct <= 60) return { label: "Medium", color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30" };
    return { label: "Low", color: "bg-blue-500/10 text-blue-400 border-blue-500/30" };
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-yellow-500/10 to-yellow-600/5 border-yellow-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-yellow-500/20">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Low Stock Products</p>
                <p className="text-xl font-bold text-yellow-400">{data.summary.total_low_stock_products}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-red-500/10 to-red-600/5 border-red-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-red-500/20">
                <AlertTriangle className="h-5 w-5 text-red-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Critical</p>
                <p className="text-xl font-bold text-red-400">{data.summary.critical_count}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-orange-500/10 to-orange-600/5 border-orange-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-500/20">
                <Package className="h-5 w-5 text-orange-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Out of Stock</p>
                <p className="text-xl font-bold text-orange-400">{data.summary.out_of_stock_count}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-blue-500/10 to-blue-600/5 border-blue-500/20">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Package className="h-5 w-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">Total Restock Qty</p>
                <p className="text-xl font-bold text-blue-400">{data.summary.total_recommended_order_quantity}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Info */}
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Calendar className="h-4 w-4" />
        <span>Threshold: {data.threshold_percentage}% of reorder level</span>
        <Separator orientation="vertical" className="h-4" />
        <span>Generated: {new Date(data.generated_at).toLocaleString()}</span>
      </div>

      {/* Items Table */}
      {data.items && data.items.length > 0 && (
        <Card className="bg-card/50 border-border/50">
          <CardHeader className="pb-3">
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-400" />
              Items Requiring Attention
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left p-3 font-medium text-muted-foreground">Product</th>
                    <th className="text-center p-3 font-medium text-muted-foreground">Priority</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Current</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Reorder Level</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Stock %</th>
                    <th className="text-right p-3 font-medium text-muted-foreground">Recommended Order</th>
                  </tr>
                </thead>
                <tbody>
                  {data.items.map((item) => {
                    const priority = getPriorityFromPercentage(Number(item.stock_percentage));
                    return (
                      <tr key={item.product_id} className="border-b border-border/30 hover:bg-muted/30">
                        <td className="p-3">
                          <div>
                            <p className="font-medium">{item.product_name}</p>
                            <p className="text-xs text-muted-foreground capitalize">{item.category?.replace("_", " ")}</p>
                          </div>
                        </td>
                        <td className="p-3 text-center">
                          <Badge className={cn("border uppercase", priority.color)}>{priority.label}</Badge>
                        </td>
                        <td className={cn("p-3 text-right font-medium", item.current_stock === 0 ? "text-red-400" : "")}>{item.current_stock}</td>
                        <td className="p-3 text-right text-muted-foreground">{item.reorder_level}</td>
                        <td
                          className={cn(
                            "p-3 text-right font-medium",
                            Number(item.stock_percentage) <= 10 ? "text-red-400" : Number(item.stock_percentage) <= 30 ? "text-orange-400" : "text-yellow-400",
                          )}
                        >
                          {Number(item.stock_percentage).toFixed(1)}%
                        </td>
                        <td className="p-3 text-right font-medium text-orange-400">+{item.recommended_order_quantity}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

// ============= Main Report Display Component =============
interface ReportDisplayProps {
  reportType: ReportType;
  data: Record<string, unknown>;
}

export function ReportDisplay({ reportType, data }: ReportDisplayProps) {
  switch (reportType) {
    case "SALES":
      return <SalesReportDisplay data={data as unknown as SalesReportData} />;
    case "INVENTORY":
      return <InventoryReportDisplay data={data as unknown as InventoryReportData} />;
    case "PRODUCT_PERFORMANCE":
      return <ProductPerformanceDisplay data={data as unknown as ProductPerformanceData} />;
    case "LOW_STOCK":
      return <LowStockReportDisplay data={data as unknown as LowStockData} />;
    default:
      // Fallback to JSON display for unknown types
      return (
        <Card className="bg-card/50 border-border/50">
          <CardContent className="p-4">
            <pre className="bg-background/50 p-4 rounded-lg overflow-auto text-sm max-h-[400px]">{JSON.stringify(data, null, 2)}</pre>
          </CardContent>
        </Card>
      );
  }
}
