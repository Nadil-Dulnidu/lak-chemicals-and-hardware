"use client";

import { useEffect, useState, useCallback } from "react";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { productActions } from "@/lib/actions";
import { LowStockAlert, Product } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { AlertTriangle, Package, TrendingDown, RefreshCw, Pencil } from "lucide-react";
import { cn } from "@/lib/utils";

const priorityColors = {
  critical: "bg-red-500/10 text-red-400 border-red-500/30",
  high: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  low: "bg-blue-500/10 text-blue-400 border-blue-500/30",
};

export default function AdminInventoryPage() {
  const [alerts, setAlerts] = useState<LowStockAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [threshold, setThreshold] = useState(10);
  const [selectedProduct, setSelectedProduct] = useState<{
    id: string;
    name: string;
    currentStock: number;
  } | null>(null);
  const [newStock, setNewStock] = useState(0);
  const [isUpdating, setIsUpdating] = useState(false);

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await productActions.getLowStockAlerts(threshold, 100);
      setAlerts(response);
    } catch (error) {
      toast.error("Failed to fetch low stock alerts");
    } finally {
      setIsLoading(false);
    }
  }, [threshold]);

  useEffect(() => {
    fetchAlerts();
  }, [fetchAlerts]);

  const handleUpdateStock = async () => {
    if (!selectedProduct) return;

    setIsUpdating(true);
    try {
      await productActions.update(selectedProduct.id, { stock_qty: newStock });
      toast.success(`Stock updated for ${selectedProduct.name}`);
      setSelectedProduct(null);
      fetchAlerts();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update stock");
    } finally {
      setIsUpdating(false);
    }
  };

  const criticalCount = alerts.filter((a) => a.priority === "critical").length;
  const highCount = alerts.filter((a) => a.priority === "high").length;
  const mediumCount = alerts.filter((a) => a.priority === "medium").length;

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex justify-center items-center min-h-[60vh]">
          <Spinner className="h-8 w-8" />
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Inventory Management</h1>
            <p className="text-muted-foreground">Monitor stock levels and manage reorders</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Threshold:</span>
              <Input type="number" value={threshold} onChange={(e) => setThreshold(parseInt(e.target.value) || 10)} className="w-20" min={1} />
            </div>
            <Button variant="outline" onClick={fetchAlerts} className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Alerts</p>
                <p className="text-2xl font-bold">{alerts.length}</p>
              </div>
              <div className="p-3 rounded-xl bg-orange-500/10">
                <AlertTriangle className="h-5 w-5 text-orange-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Critical</p>
                <p className="text-2xl font-bold text-red-400">{criticalCount}</p>
              </div>
              <div className="p-3 rounded-xl bg-red-500/10">
                <TrendingDown className="h-5 w-5 text-red-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">High Priority</p>
                <p className="text-2xl font-bold text-orange-400">{highCount}</p>
              </div>
              <div className="p-3 rounded-xl bg-orange-500/10">
                <AlertTriangle className="h-5 w-5 text-orange-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Medium Priority</p>
                <p className="text-2xl font-bold text-yellow-400">{mediumCount}</p>
              </div>
              <div className="p-3 rounded-xl bg-yellow-500/10">
                <AlertTriangle className="h-5 w-5 text-yellow-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Alerts Table */}
        <Card className="bg-card/50 border-border/50">
          <CardHeader>
            <CardTitle className="text-lg">Low Stock Alerts</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left p-4 font-medium text-muted-foreground">Product</th>
                    <th className="text-center p-4 font-medium text-muted-foreground">Priority</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Current Stock</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Reorder Level</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Qty Needed</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {alerts.map((alert) => (
                    <tr key={alert.product_id} className="border-b border-border/50 hover:bg-muted/30">
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                            <Package className="h-5 w-5 text-muted-foreground/50" />
                          </div>
                          <p className="font-medium">{alert.product_name}</p>
                        </div>
                      </td>
                      <td className="p-4 text-center">
                        <Badge className={cn("border uppercase text-xs", priorityColors[alert.priority])}>{alert.priority}</Badge>
                      </td>
                      <td className="p-4 text-right">
                        <span className={cn("font-medium", alert.current_stock === 0 && "text-red-400")}>{alert.current_stock}</span>
                      </td>
                      <td className="p-4 text-right text-muted-foreground">{alert.reorder_level}</td>
                      <td className="p-4 text-right font-medium text-orange-400">+{alert.quantity_needed}</td>
                      <td className="p-4 text-right">
                        <Button
                          variant="outline"
                          size="sm"
                          className="gap-2"
                          onClick={() => {
                            setSelectedProduct({
                              id: alert.product_id,
                              name: alert.product_name,
                              currentStock: alert.current_stock,
                            });
                            setNewStock(alert.current_stock + alert.quantity_needed);
                          }}
                        >
                          <Pencil className="h-3 w-3" />
                          Update Stock
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {alerts.length === 0 && (
              <div className="py-12 text-center">
                <Package className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                <p className="text-muted-foreground">All stock levels are healthy</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Update Stock Dialog */}
        <Dialog open={!!selectedProduct} onOpenChange={() => setSelectedProduct(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Update Stock</DialogTitle>
            </DialogHeader>
            {selectedProduct && (
              <div className="space-y-4">
                <div>
                  <p className="font-medium">{selectedProduct.name}</p>
                  <p className="text-sm text-muted-foreground">Current stock: {selectedProduct.currentStock}</p>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">New Stock Quantity</label>
                  <Input type="number" value={newStock} onChange={(e) => setNewStock(parseInt(e.target.value) || 0)} min={0} />
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setSelectedProduct(null)}>
                    Cancel
                  </Button>
                  <Button className="flex-1 bg-orange-500 hover:bg-orange-600" onClick={handleUpdateStock} disabled={isUpdating}>
                    {isUpdating ? "Updating..." : "Update"}
                  </Button>
                </div>
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </AdminLayout>
  );
}
