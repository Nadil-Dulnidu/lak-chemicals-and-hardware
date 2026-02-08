"use client";

import { useState } from "react";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { reportActions } from "@/lib/actions";
import { SalesReportData, InventoryReportData } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { BarChart3, Package, TrendingUp, AlertTriangle, DollarSign, ShoppingBag, Calendar } from "lucide-react";
import { cn } from "@/lib/utils";

export default function AdminReportsPage() {
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("sales");

  // Sales Report State
  const [salesStartDate, setSalesStartDate] = useState("");
  const [salesEndDate, setSalesEndDate] = useState("");
  const [salesGroupBy, setSalesGroupBy] = useState<"day" | "week" | "month">("day");
  const [salesReport, setSalesReport] = useState<SalesReportData | null>(null);

  // Inventory Report State
  const [inventoryLowStockOnly, setInventoryLowStockOnly] = useState(false);
  const [inventoryReport, setInventoryReport] = useState<InventoryReportData | null>(null);

  const generateSalesReport = async () => {
    if (!salesStartDate || !salesEndDate) {
      toast.error("Please select start and end dates");
      return;
    }

    setIsLoading(true);
    try {
      const report = await reportActions.generateSales({
        start_date: salesStartDate,
        end_date: salesEndDate,
        group_by: salesGroupBy,
      });
      setSalesReport(report);
      toast.success("Sales report generated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to generate report");
    } finally {
      setIsLoading(false);
    }
  };

  const generateInventoryReport = async () => {
    setIsLoading(true);
    try {
      const report = await reportActions.generateInventory({
        low_stock_only: inventoryLowStockOnly,
      });
      setInventoryReport(report);
      toast.success("Inventory report generated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to generate report");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold mb-2">Reports & Analytics</h1>
          <p className="text-muted-foreground">Generate and view business reports</p>
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-card/50">
            <TabsTrigger value="sales" className="gap-2">
              <TrendingUp className="h-4 w-4" />
              Sales
            </TabsTrigger>
            <TabsTrigger value="inventory" className="gap-2">
              <Package className="h-4 w-4" />
              Inventory
            </TabsTrigger>
          </TabsList>

          {/* Sales Report Tab */}
          <TabsContent value="sales" className="space-y-6">
            {/* Filters */}
            <Card className="bg-card/50 border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Generate Sales Report</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap items-end gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Start Date</label>
                    <Input type="date" value={salesStartDate} onChange={(e) => setSalesStartDate(e.target.value)} className="w-40" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">End Date</label>
                    <Input type="date" value={salesEndDate} onChange={(e) => setSalesEndDate(e.target.value)} className="w-40" />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Group By</label>
                    <Select value={salesGroupBy} onValueChange={(v) => setSalesGroupBy(v as "day" | "week" | "month")}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="day">Day</SelectItem>
                        <SelectItem value="week">Week</SelectItem>
                        <SelectItem value="month">Month</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button onClick={generateSalesReport} disabled={isLoading} className="bg-orange-500 hover:bg-orange-600">
                    {isLoading ? <Spinner className="h-4 w-4 mr-2" /> : <BarChart3 className="h-4 w-4 mr-2" />}
                    Generate Report
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Sales Report Results */}
            {salesReport && (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card className="bg-card/50 border-border/50">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Total Sales</p>
                        <p className="text-2xl font-bold">{salesReport.summary.total_sales}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-blue-500/10">
                        <ShoppingBag className="h-5 w-5 text-blue-400" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-card/50 border-border/50">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Total Revenue</p>
                        <p className="text-2xl font-bold">LKR {salesReport.summary.total_revenue.toLocaleString()}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-green-500/10">
                        <DollarSign className="h-5 w-5 text-green-400" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-card/50 border-border/50">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Quantity Sold</p>
                        <p className="text-2xl font-bold">{salesReport.summary.total_quantity}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-purple-500/10">
                        <Package className="h-5 w-5 text-purple-400" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-card/50 border-border/50">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Avg Sale Value</p>
                        <p className="text-2xl font-bold">LKR {salesReport.summary.average_sale_value.toLocaleString()}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-orange-500/10">
                        <TrendingUp className="h-5 w-5 text-orange-400" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Sales by Period */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader>
                    <CardTitle className="text-lg">Sales by Period</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-border/50">
                            <th className="text-left p-3 font-medium text-muted-foreground">Period</th>
                            <th className="text-right p-3 font-medium text-muted-foreground">Sales</th>
                            <th className="text-right p-3 font-medium text-muted-foreground">Quantity</th>
                            <th className="text-right p-3 font-medium text-muted-foreground">Revenue</th>
                          </tr>
                        </thead>
                        <tbody>
                          {salesReport.items.map((item, index) => (
                            <tr key={index} className="border-b border-border/50">
                              <td className="p-3 flex items-center gap-2">
                                <Calendar className="h-4 w-4 text-muted-foreground" />
                                {item.period}
                              </td>
                              <td className="p-3 text-right">{item.total_sales}</td>
                              <td className="p-3 text-right">{item.total_quantity}</td>
                              <td className="p-3 text-right font-medium">LKR {item.total_revenue.toLocaleString()}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

          {/* Inventory Report Tab */}
          <TabsContent value="inventory" className="space-y-6">
            {/* Filters */}
            <Card className="bg-card/50 border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Generate Inventory Report</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-end gap-4">
                  <div className="flex items-center gap-2">
                    <input type="checkbox" id="lowStockOnly" checked={inventoryLowStockOnly} onChange={(e) => setInventoryLowStockOnly(e.target.checked)} className="h-4 w-4 rounded border-border" />
                    <label htmlFor="lowStockOnly" className="text-sm">
                      Low stock items only
                    </label>
                  </div>
                  <Button onClick={generateInventoryReport} disabled={isLoading} className="bg-orange-500 hover:bg-orange-600">
                    {isLoading ? <Spinner className="h-4 w-4 mr-2" /> : <Package className="h-4 w-4 mr-2" />}
                    Generate Report
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Inventory Report Results */}
            {inventoryReport && (
              <>
                {/* Summary Cards */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  <Card className="bg-card/50 border-border/50">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Total Products</p>
                        <p className="text-2xl font-bold">{inventoryReport.summary.total_products}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-blue-500/10">
                        <Package className="h-5 w-5 text-blue-400" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-card/50 border-border/50">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Stock Value</p>
                        <p className="text-2xl font-bold">LKR {inventoryReport.summary.total_stock_value.toLocaleString()}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-green-500/10">
                        <DollarSign className="h-5 w-5 text-green-400" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-card/50 border-border/50">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Low Stock</p>
                        <p className="text-2xl font-bold">{inventoryReport.summary.low_stock_count}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-yellow-500/10">
                        <AlertTriangle className="h-5 w-5 text-yellow-400" />
                      </div>
                    </CardContent>
                  </Card>
                  <Card className="bg-card/50 border-border/50">
                    <CardContent className="p-4 flex items-center justify-between">
                      <div>
                        <p className="text-sm text-muted-foreground">Out of Stock</p>
                        <p className="text-2xl font-bold">{inventoryReport.summary.out_of_stock_count}</p>
                      </div>
                      <div className="p-3 rounded-xl bg-red-500/10">
                        <AlertTriangle className="h-5 w-5 text-red-400" />
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Inventory Table */}
                <Card className="bg-card/50 border-border/50">
                  <CardHeader>
                    <CardTitle className="text-lg">Inventory Details</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b border-border/50">
                            <th className="text-left p-3 font-medium text-muted-foreground">Product</th>
                            <th className="text-left p-3 font-medium text-muted-foreground">Category</th>
                            <th className="text-right p-3 font-medium text-muted-foreground">Stock</th>
                            <th className="text-right p-3 font-medium text-muted-foreground">Reorder Level</th>
                            <th className="text-right p-3 font-medium text-muted-foreground">Value</th>
                            <th className="text-center p-3 font-medium text-muted-foreground">Status</th>
                          </tr>
                        </thead>
                        <tbody>
                          {inventoryReport.items.map((item) => (
                            <tr key={item.product_id} className="border-b border-border/50">
                              <td className="p-3">
                                <p className="font-medium">{item.product_name}</p>
                              </td>
                              <td className="p-3 text-muted-foreground">{item.category}</td>
                              <td className="p-3 text-right">{item.current_stock}</td>
                              <td className="p-3 text-right">{item.reorder_level}</td>
                              <td className="p-3 text-right font-medium">LKR {item.stock_value.toLocaleString()}</td>
                              <td className="p-3 text-center">
                                <Badge
                                  className={cn(
                                    "border",
                                    item.status === "OK"
                                      ? "bg-green-500/10 text-green-400 border-green-500/30"
                                      : item.status === "LOW"
                                        ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/30"
                                        : "bg-red-500/10 text-red-400 border-red-500/30",
                                  )}
                                >
                                  {item.status === "OUT_OF_STOCK" ? "Out" : item.status}
                                </Badge>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </AdminLayout>
  );
}
