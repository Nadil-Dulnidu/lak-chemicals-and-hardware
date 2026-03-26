"use client";

import { useRef, useState } from "react";
import html2canvas from "html2canvas-pro";
import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { DollarSign, ShoppingBag, TrendingUp, Package, AlertTriangle, BarChart3, Calendar, Download } from "lucide-react";
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

// ============= Downloadable Wrapper Component =============
export function DownloadableReport({ children, fileName = "report", data, reportType }: { children: React.ReactNode; fileName?: string; data?: Record<string, unknown>; reportType?: string }) {
  const reportRef = useRef<HTMLDivElement>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const downloadPDF = async () => {
    if (!data || !reportType) {
      // Fallback to html2canvas if no data mapping
      const element = reportRef.current;
      if (!element) return;
      setIsDownloading(true);
      try {
        await new Promise((resolve) => setTimeout(resolve, 100));
        const canvas = await html2canvas(element, {
          scale: 2,
          useCORS: true,
          backgroundColor: "#ffffff",
        });

        const imgData = canvas.toDataURL("image/png");
        const pdf = new jsPDF("p", "mm", "a4");
        const pdfWidth = pdf.internal.pageSize.getWidth();
        const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
        const pageHeight = pdf.internal.pageSize.getHeight();
        let heightLeft = pdfHeight;
        let position = 0;

        pdf.addImage(imgData, "PNG", 0, position, pdfWidth, pdfHeight);
        heightLeft -= pageHeight;
        while (heightLeft >= 0) {
          position = heightLeft - pdfHeight;
          pdf.addPage();
          pdf.addImage(imgData, "PNG", 0, position, pdfWidth, pdfHeight);
          heightLeft -= pageHeight;
        }
        pdf.save(`${fileName}.pdf`);
      } catch (error) {
        console.error("PDF generation failed", error);
      } finally {
        setIsDownloading(false);
      }
      return;
    }

    // NATIVE PDF GENERATION using jspdf-autotable
    setIsDownloading(true);
    try {
      const doc = new jsPDF("p", "mm", "a4");
      const pageWidth = doc.internal.pageSize.width;

      // Header
      doc.setFontSize(22);
      doc.setTextColor(30);
      doc.text("Lak Chemicals & Hardware", 14, 22);

      doc.setFontSize(14);
      doc.setTextColor(80);
      const textTitle = fileName.replace(/-/g, " ");
      doc.text(textTitle, 14, 32);

      doc.setFontSize(10);
      doc.setTextColor(120);
      doc.text(`Generated at: ${new Date().toLocaleString()}`, 14, 40);

      let currentY = 50;

      if (reportType === "SALES") {
        const sales = data as unknown as SalesReportData;

        doc.setFontSize(12);
        doc.setTextColor(0);
        doc.text("Summary", 14, currentY);
        currentY += 6;

        autoTable(doc, {
          startY: currentY,
          head: [["Total Revenue", "Total Sales", "Items Sold", "Avg Sale Value"]],
          body: [
            [
              `LKR ${sales.summary.total_revenue?.toLocaleString() || 0}`,
              sales.summary.total_sales?.toString() || "0",
              sales.summary.total_quantity?.toString() || "0",
              `LKR ${sales.summary.average_sale_value?.toLocaleString() || 0}`,
            ],
          ],
          margin: { left: 14, right: 14 },
          theme: "grid",
          headStyles: { fillColor: [41, 128, 185] },
        });
        currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;

        if (sales.items && sales.items.length > 0) {
          doc.setFontSize(12);
          doc.text("Sales by Period", 14, currentY);
          currentY += 6;
          autoTable(doc, {
            startY: currentY,
            head: [["Period", "Sales", "Quantity", "Revenue"]],
            body: sales.items.map((item) => [item.period, item.total_sales?.toString(), item.total_quantity?.toString(), `LKR ${item.total_revenue?.toLocaleString()}`]),
            margin: { left: 14, right: 14 },
            theme: "striped",
            headStyles: { fillColor: [41, 128, 185] },
          });
          currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;
        }

        if (sales.product_breakdown && sales.product_breakdown.length > 0) {
          doc.setFontSize(12);
          doc.text("Top Products", 14, currentY);
          currentY += 6;
          autoTable(doc, {
            startY: currentY,
            head: [["Rank", "Product", "Orders", "Qty Sold", "Revenue (LKR)"]],
            body: sales.product_breakdown.slice(0, 10).map((p, i) => [
              `#${i + 1}`,
              p.product_name,
              p.sales_count?.toString() || "0",
              p.quantity_sold?.toString() || "0",
              p.revenue?.toLocaleString() || "0",
            ]),
            margin: { left: 14, right: 14 },
            theme: "striped",
            styles: { fontSize: 9 },
            headStyles: { fillColor: [41, 128, 185] },
          });
          currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;
        }

        if (sales.category_breakdown && sales.category_breakdown.length > 0) {
          doc.setFontSize(12);
          doc.text("Sales by Category", 14, currentY);
          currentY += 6;
          autoTable(doc, {
            startY: currentY,
            head: [["Category", "Orders", "Qty Sold", "Revenue (LKR)"]],
            body: sales.category_breakdown.map((cat) => [
              cat.category?.replace("_", " ") || "-",
              cat.sales_count?.toString() || "0",
              cat.quantity_sold?.toString() || "0",
              cat.revenue?.toLocaleString() || "0",
            ]),
            margin: { left: 14, right: 14 },
            theme: "striped",
            styles: { fontSize: 9 },
            headStyles: { fillColor: [41, 128, 185] },
          });
          currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;
        }
      } else if (reportType === "INVENTORY") {
        const inv = data as unknown as InventoryReportData;

        doc.setFontSize(12);
        doc.text("Summary", 14, currentY);
        currentY += 6;

        autoTable(doc, {
          startY: currentY,
          head: [["Total Products", "Stock Value", "Low Stock", "Out of Stock"]],
          body: [
            [inv.summary.total_products?.toString(), `LKR ${inv.summary.total_stock_value?.toLocaleString()}`, inv.summary.low_stock_count?.toString(), inv.summary.out_of_stock_count?.toString()],
          ],
          margin: { left: 14 },
          theme: "grid",
          headStyles: { fillColor: [39, 174, 96] },
        });
        currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;

        if (inv.low_stock_items && inv.low_stock_items.length > 0) {
          doc.setFontSize(12);
          doc.text(`Low Stock Items (${inv.low_stock_items.length})`, 14, currentY);
          currentY += 6;
          autoTable(doc, {
            startY: currentY,
            head: [["Product", "Category", "Status", "Current Stock", "Reorder Level"]],
            body: inv.low_stock_items.map((item) => [
              item.product_name,
              item.category?.replace("_", " ") || "N/A",
              item.status.replace("_", " "),
              item.current_stock?.toString(),
              item.reorder_level?.toString(),
            ]),
            margin: { left: 14, right: 14 },
            styles: { fontSize: 9 },
            theme: "striped",
            headStyles: { fillColor: [243, 156, 18] },
          });
          currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;
        }

        if (inv.items && inv.items.length > 0) {
          doc.setFontSize(12);
          doc.text("All Products", 14, currentY);
          currentY += 6;

          autoTable(doc, {
            startY: currentY,
            head: [["Product", "Category", "Status", "Stock", "Value (LKR)"]],
            body: inv.items.map((item) => [
              item.product_name,
              item.category?.replace("_", " ") || "N/A",
              item.status.replace("_", " "),
              item.current_stock?.toString(),
              item.stock_value?.toLocaleString() || "0",
            ]),
            margin: { left: 14, right: 14 },
            styles: { fontSize: 9 },
            theme: "striped",
            headStyles: { fillColor: [39, 174, 96] },
          });
        }
      } else if (reportType === "PRODUCT_PERFORMANCE") {
        const perf = data as unknown as ProductPerformanceData;

        if (perf.summary) {
          doc.setFontSize(12);
          doc.text("Summary", 14, currentY);
          currentY += 6;

          autoTable(doc, {
            startY: currentY,
            head: [["Products Analyzed", "Total Revenue", "Total Qty Sold"]],
            body: [[perf.summary.top_product_count?.toString() || "0", `LKR ${perf.summary.total_revenue?.toLocaleString() || 0}`, perf.summary.total_quantity_sold?.toString() || "0"]],
            theme: "grid",
            headStyles: { fillColor: [142, 68, 173] },
          });
          currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;
        }

        if (perf.top_products && perf.top_products.length > 0) {
          doc.setFontSize(12);
          doc.text("Top Performing Products", 14, currentY);
          currentY += 6;
          autoTable(doc, {
            startY: currentY,
            head: [["Rank", "Product", "Category", "Orders", "Avg Qty/Order", "Qty Sold", "Revenue (LKR)"]],
            body: perf.top_products.map((p, i) => [
              `#${i + 1}`,
              p.product_name,
              p.category?.replace("_", " ") || "-",
              p.number_of_orders?.toString() || "0",
              Number(p.average_order_quantity)?.toFixed(1) || "0",
              p.total_quantity_sold?.toString() || "0",
              Number(p.total_revenue)?.toLocaleString() || "0",
            ]),
            theme: "striped",
            styles: { fontSize: 9 },
            headStyles: { fillColor: [142, 68, 173] },
          });
          currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;
        }

        if (perf.category_performance && perf.category_performance.length > 0) {
          doc.setFontSize(12);
          doc.text("Category Performance", 14, currentY);
          currentY += 6;
          autoTable(doc, {
            startY: currentY,
            head: [["Category", "Qty Sold", "Unique Products", "Revenue (LKR)"]],
            body: perf.category_performance.map((cat) => [
              cat.category?.replace("_", " ") || "-",
              cat.total_quantity?.toString() || "0",
              cat.unique_products?.toString() || "0",
              cat.total_revenue?.toLocaleString() || "0",
            ]),
            theme: "striped",
            styles: { fontSize: 9 },
            headStyles: { fillColor: [142, 68, 173] },
          });
          currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;
        }
      } else if (reportType === "LOW_STOCK") {
        const low = data as unknown as LowStockData;

        doc.setFontSize(12);
        doc.text("Summary", 14, currentY);
        currentY += 6;

        autoTable(doc, {
          startY: currentY,
          head: [["Low Stock Items", "Critical", "Out of Stock", "Recommended Restock Qty"]],
          body: [
            [
              low.summary.total_low_stock_products?.toString() || "0",
              low.summary.critical_count?.toString() || "0",
              low.summary.out_of_stock_count?.toString() || "0",
              low.summary.total_recommended_order_quantity?.toString() || "0",
            ],
          ],
          theme: "grid",
          headStyles: { fillColor: [211, 84, 0] },
        });
        currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;

        if (low.items) {
          doc.text("Items Requiring Attention", 14, currentY);
          currentY += 6;
          autoTable(doc, {
            startY: currentY,
            head: [["Product", "Category", "Current", "Reorder Level", "Stock %", "Recommend"]],
            body: low.items.map((item) => [
              item.product_name,
              item.category?.replace("_", " ") || "-",
              item.current_stock?.toString() || "0",
              item.reorder_level?.toString() || "0",
              `${Number(item.stock_percentage).toFixed(1)}%`,
              `+${item.recommended_order_quantity}`,
            ]),
            theme: "striped",
            styles: { fontSize: 9 },
          });
          currentY = (doc as unknown as { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 15;
        }
      }

      // Add footer
      const pageCount = (doc.internal as unknown as { getNumberOfPages: () => number }).getNumberOfPages();
      for (let i = 1; i <= pageCount; i++) {
        doc.setPage(i);
        doc.setFontSize(8);
        doc.setTextColor(150);
        doc.text(`Page ${i} of ${pageCount}`, pageWidth - 20, doc.internal.pageSize.height - 10, { align: "right" });
      }

      doc.save(`${fileName}.pdf`);
    } catch (error) {
      console.error("Native PDF generation failed", error);
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <Button onClick={downloadPDF} disabled={isDownloading} variant="outline" className="gap-2 border-orange-500/30 text-orange-500 hover:bg-orange-500 hover:text-white transition-colors">
          <Download className="h-4 w-4" />
          {isDownloading ? "Generating PDF..." : "Download as PDF"}
        </Button>
      </div>
      <div className="p-6 bg-background rounded-xl border border-border" ref={reportRef}>
        {children}
      </div>
    </div>
  );
}
