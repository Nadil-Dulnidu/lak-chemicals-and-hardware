"use client";

import { useEffect, useState, useCallback } from "react";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { productActions, inventoryActions } from "@/lib/actions";
import { LowStockAlert, Product, StockMovement, StockMovementListResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { AlertTriangle, Package, TrendingDown, TrendingUp, RefreshCw, Pencil, Plus, ArrowUpCircle, ArrowDownCircle, History, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";

const priorityColors = {
  critical: "bg-red-500/10 text-red-400 border-red-500/30",
  high: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  medium: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  low: "bg-blue-500/10 text-blue-400 border-blue-500/30",
};

export default function AdminInventoryPage() {
  const [activeTab, setActiveTab] = useState("movements");

  // Low Stock Alerts State
  const [alerts, setAlerts] = useState<LowStockAlert[]>([]);
  const [isLoadingAlerts, setIsLoadingAlerts] = useState(true);
  const [threshold, setThreshold] = useState(10);

  // Stock Movements State
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [isLoadingMovements, setIsLoadingMovements] = useState(true);
  const [movementsTotal, setMovementsTotal] = useState(0);
  const [movementFilter, setMovementFilter] = useState<"all" | "IN" | "OUT">("all");

  // Products for dropdown
  const [products, setProducts] = useState<Product[]>([]);

  // Dialogs
  const [showRecordDialog, setShowRecordDialog] = useState(false);
  const [showAdjustDialog, setShowAdjustDialog] = useState(false);

  // Record Movement Form
  const [selectedProductId, setSelectedProductId] = useState("");
  const [movementType, setMovementType] = useState<"IN" | "OUT">("IN");
  const [quantity, setQuantity] = useState<number>(0);
  const [reference, setReference] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Adjust Stock Form
  const [adjustProductId, setAdjustProductId] = useState("");
  const [targetQuantity, setTargetQuantity] = useState<number>(0);
  const [adjustReference, setAdjustReference] = useState("");

  // Update Stock (for alerts)
  const [selectedAlert, setSelectedAlert] = useState<LowStockAlert | null>(null);
  const [newStock, setNewStock] = useState(0);

  // Load data on mount
  useEffect(() => {
    loadProducts();
  }, []);

  const loadProducts = async () => {
    try {
      const response = await productActions.getAll(0, 500, true);
      setProducts(response.products);
    } catch {
      console.error("Failed to load products");
    }
  };

  const loadMovements = useCallback(async () => {
    setIsLoadingMovements(true);
    try {
      let response: StockMovementListResponse;
      if (movementFilter === "all") {
        response = await inventoryActions.getAllMovements(0, 100);
      } else {
        response = await inventoryActions.filterMovements({
          movement_type: movementFilter,
          limit: 100,
        });
      }
      setMovements(response.movements);
      setMovementsTotal(response.total);
    } catch (error) {
      console.error("Failed to load movements:", error);
      toast.error("Failed to load stock movements");
    } finally {
      setIsLoadingMovements(false);
    }
  }, [movementFilter]);

  useEffect(() => {
    loadMovements();
  }, [loadMovements]);

  const loadAlerts = useCallback(async () => {
    setIsLoadingAlerts(true);
    try {
      const response = await productActions.getLowStockAlerts(threshold, 100);
      setAlerts(response);
    } catch {
      toast.error("Failed to fetch low stock alerts");
    } finally {
      setIsLoadingAlerts(false);
    }
  }, [threshold]);

  useEffect(() => {
    loadAlerts();
  }, [loadAlerts]);

  const handleRecordMovement = async () => {
    if (!selectedProductId || quantity <= 0) {
      toast.error("Please select a product and enter a valid quantity");
      return;
    }

    setIsSubmitting(true);
    try {
      await inventoryActions.recordMovement({
        product_id: selectedProductId,
        movement_type: movementType,
        quantity,
        reference: reference || undefined,
      });
      toast.success(`Stock ${movementType === "IN" ? "added" : "removed"} successfully!`);
      setShowRecordDialog(false);
      resetRecordForm();
      loadMovements();
      loadAlerts();
      loadProducts();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to record movement");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleAdjustStock = async () => {
    if (!adjustProductId) {
      toast.error("Please select a product");
      return;
    }

    setIsSubmitting(true);
    try {
      await inventoryActions.adjustStock({
        product_id: adjustProductId,
        target_quantity: targetQuantity,
        reference: adjustReference || undefined,
      });
      toast.success("Stock adjusted successfully!");
      setShowAdjustDialog(false);
      resetAdjustForm();
      loadMovements();
      loadAlerts();
      loadProducts();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to adjust stock");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUpdateStockFromAlert = async () => {
    if (!selectedAlert) return;

    setIsSubmitting(true);
    try {
      await productActions.update(selectedAlert.product_id, { stock_qty: newStock });
      toast.success(`Stock updated for ${selectedAlert.product_name}`);
      setSelectedAlert(null);
      loadAlerts();
      loadProducts();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update stock");
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDeleteMovement = async (movementId: number) => {
    if (!confirm("Delete this movement record? Note: This only deletes the history record, it does NOT reverse the stock change.")) {
      return;
    }

    try {
      await inventoryActions.deleteMovement(movementId);
      toast.success("Movement record deleted");
      loadMovements();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to delete movement");
    }
  };

  const resetRecordForm = () => {
    setSelectedProductId("");
    setMovementType("IN");
    setQuantity(0);
    setReference("");
  };

  const resetAdjustForm = () => {
    setAdjustProductId("");
    setTargetQuantity(0);
    setAdjustReference("");
  };

  const criticalCount = alerts.filter((a) => a.priority === "critical").length;
  const highCount = alerts.filter((a) => a.priority === "high").length;

  const getProductName = (productId: string) => {
    const product = products.find((p) => p.id === productId);
    return product?.name || "Unknown Product";
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Inventory Management</h1>
            <p className="text-muted-foreground">Track stock movements, manage levels, and monitor alerts</p>
          </div>
          <div className="flex gap-2">
            <Button onClick={() => setShowRecordDialog(true)} className="gap-2 bg-orange-500 hover:bg-orange-600">
              <Plus className="h-4 w-4" />
              Record Movement
            </Button>
            <Button onClick={() => setShowAdjustDialog(true)} variant="outline" className="gap-2">
              <Pencil className="h-4 w-4" />
              Adjust Stock
            </Button>
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Products</p>
                <p className="text-2xl font-bold">{products.length}</p>
              </div>
              <div className="p-3 rounded-xl bg-blue-500/10">
                <Package className="h-5 w-5 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Movements</p>
                <p className="text-2xl font-bold">{movementsTotal}</p>
              </div>
              <div className="p-3 rounded-xl bg-purple-500/10">
                <History className="h-5 w-5 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Critical Alerts</p>
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
        </div>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="bg-card/50">
            <TabsTrigger value="movements" className="gap-2">
              <History className="h-4 w-4" />
              Stock Movements
            </TabsTrigger>
            <TabsTrigger value="alerts" className="gap-2">
              <AlertTriangle className="h-4 w-4" />
              Low Stock Alerts
              {alerts.length > 0 && <Badge className="ml-1 bg-red-500/20 text-red-400 border-red-500/30">{alerts.length}</Badge>}
            </TabsTrigger>
          </TabsList>

          {/* Stock Movements Tab */}
          <TabsContent value="movements" className="space-y-4">
            <Card className="bg-card/50 border-border/50">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Movement History</CardTitle>
                  <div className="flex items-center gap-2">
                    <Select value={movementFilter} onValueChange={(v) => setMovementFilter(v as "all" | "IN" | "OUT")}>
                      <SelectTrigger className="w-32">
                        <SelectValue placeholder="Filter" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All</SelectItem>
                        <SelectItem value="IN">Stock In</SelectItem>
                        <SelectItem value="OUT">Stock Out</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button variant="outline" size="sm" onClick={loadMovements}>
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {isLoadingMovements ? (
                  <div className="flex justify-center py-12">
                    <Spinner className="h-8 w-8" />
                  </div>
                ) : movements.length === 0 ? (
                  <div className="py-12 text-center">
                    <History className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                    <p className="text-muted-foreground">No stock movements recorded yet</p>
                    <Button onClick={() => setShowRecordDialog(true)} className="mt-4 gap-2">
                      <Plus className="h-4 w-4" />
                      Record First Movement
                    </Button>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-border/50">
                          <th className="text-left p-4 font-medium text-muted-foreground">Date</th>
                          <th className="text-left p-4 font-medium text-muted-foreground">Product</th>
                          <th className="text-center p-4 font-medium text-muted-foreground">Type</th>
                          <th className="text-right p-4 font-medium text-muted-foreground">Quantity</th>
                          <th className="text-left p-4 font-medium text-muted-foreground">Reference</th>
                          <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {movements.map((movement) => (
                          <tr key={movement.movement_id} className="border-b border-border/50 hover:bg-muted/30">
                            <td className="p-4 text-sm">
                              {new Date(movement.movement_date).toLocaleDateString()}{" "}
                              <span className="text-muted-foreground">{new Date(movement.movement_date).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</span>
                            </td>
                            <td className="p-4">
                              <div className="flex items-center gap-3">
                                <div className="h-8 w-8 rounded-lg bg-muted flex items-center justify-center">
                                  <Package className="h-4 w-4 text-muted-foreground/50" />
                                </div>
                                <span className="font-medium">{movement.product_name || getProductName(movement.product_id)}</span>
                              </div>
                            </td>
                            <td className="p-4 text-center">
                              <Badge
                                className={cn("border gap-1", movement.movement_type === "IN" ? "bg-green-500/10 text-green-400 border-green-500/30" : "bg-red-500/10 text-red-400 border-red-500/30")}
                              >
                                {movement.movement_type === "IN" ? <ArrowDownCircle className="h-3 w-3" /> : <ArrowUpCircle className="h-3 w-3" />}
                                {movement.movement_type}
                              </Badge>
                            </td>
                            <td className="p-4 text-right">
                              <span className={cn("font-medium", movement.movement_type === "IN" ? "text-green-400" : "text-red-400")}>
                                {movement.movement_type === "IN" ? "+" : "-"}
                                {movement.quantity}
                              </span>
                            </td>
                            <td className="p-4 text-muted-foreground text-sm">{movement.reference || "-"}</td>
                            <td className="p-4 text-right">
                              <Button variant="ghost" size="sm" onClick={() => handleDeleteMovement(movement.movement_id)} className="text-red-400 hover:text-red-300 hover:bg-red-500/10">
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Low Stock Alerts Tab */}
          <TabsContent value="alerts" className="space-y-4">
            <Card className="bg-card/50 border-border/50">
              <CardHeader className="pb-3">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg">Low Stock Alerts</CardTitle>
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-muted-foreground">Threshold:</span>
                      <Input type="number" value={threshold} onChange={(e) => setThreshold(parseInt(e.target.value) || 10)} className="w-20" min={1} />
                    </div>
                    <Button variant="outline" size="sm" onClick={loadAlerts}>
                      <RefreshCw className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                {isLoadingAlerts ? (
                  <div className="flex justify-center py-12">
                    <Spinner className="h-8 w-8" />
                  </div>
                ) : alerts.length === 0 ? (
                  <div className="py-12 text-center">
                    <Package className="h-12 w-12 text-muted-foreground/30 mx-auto mb-4" />
                    <p className="text-muted-foreground">All stock levels are healthy</p>
                  </div>
                ) : (
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
                                  setSelectedAlert(alert);
                                  setNewStock(alert.current_stock + alert.quantity_needed);
                                }}
                              >
                                <TrendingUp className="h-3 w-3" />
                                Restock
                              </Button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Record Movement Dialog */}
        <Dialog open={showRecordDialog} onOpenChange={setShowRecordDialog}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Plus className="h-5 w-5" />
                Record Stock Movement
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Product *</label>
                <Select value={selectedProductId} onValueChange={setSelectedProductId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((product) => (
                      <SelectItem key={product.id} value={product.id}>
                        {product.name} (Stock: {product.stock_qty})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Movement Type *</label>
                <Select value={movementType} onValueChange={(v) => setMovementType(v as "IN" | "OUT")}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="IN">
                      <span className="flex items-center gap-2">
                        <ArrowDownCircle className="h-4 w-4 text-green-400" />
                        Stock In (Receiving)
                      </span>
                    </SelectItem>
                    <SelectItem value="OUT">
                      <span className="flex items-center gap-2">
                        <ArrowUpCircle className="h-4 w-4 text-red-400" />
                        Stock Out (Dispatch)
                      </span>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Quantity *</label>
                <Input type="number" min={1} value={quantity || ""} onChange={(e) => setQuantity(parseInt(e.target.value) || 0)} placeholder="Enter quantity" />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Reference / Note</label>
                <Textarea value={reference} onChange={(e) => setReference(e.target.value)} placeholder="e.g., Invoice #12345, Return from customer, etc." rows={2} />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowRecordDialog(false);
                  resetRecordForm();
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleRecordMovement}
                disabled={isSubmitting || !selectedProductId || quantity <= 0}
                className={cn(movementType === "IN" ? "bg-green-600 hover:bg-green-700" : "bg-red-600 hover:bg-red-700")}
              >
                {isSubmitting ? <Spinner className="h-4 w-4 mr-2" /> : null}
                Record {movementType === "IN" ? "Stock In" : "Stock Out"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Adjust Stock Dialog */}
        <Dialog open={showAdjustDialog} onOpenChange={setShowAdjustDialog}>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Pencil className="h-5 w-5" />
                Adjust Stock Level
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Product *</label>
                <Select value={adjustProductId} onValueChange={setAdjustProductId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a product" />
                  </SelectTrigger>
                  <SelectContent>
                    {products.map((product) => (
                      <SelectItem key={product.id} value={product.id}>
                        {product.name} (Current: {product.stock_qty})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {adjustProductId && (
                <div className="p-3 bg-muted/50 rounded-lg">
                  <p className="text-sm text-muted-foreground">Current Stock:</p>
                  <p className="text-lg font-bold">{products.find((p) => p.id === adjustProductId)?.stock_qty || 0} units</p>
                </div>
              )}
              <div>
                <label className="text-sm font-medium mb-2 block">Target Quantity *</label>
                <Input type="number" min={0} value={targetQuantity || ""} onChange={(e) => setTargetQuantity(parseInt(e.target.value) || 0)} placeholder="Enter target stock quantity" />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Reason for Adjustment</label>
                <Textarea value={adjustReference} onChange={(e) => setAdjustReference(e.target.value)} placeholder="e.g., Inventory count correction, damaged goods, etc." rows={2} />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => {
                  setShowAdjustDialog(false);
                  resetAdjustForm();
                }}
              >
                Cancel
              </Button>
              <Button onClick={handleAdjustStock} disabled={isSubmitting || !adjustProductId} className="bg-orange-500 hover:bg-orange-600">
                {isSubmitting ? <Spinner className="h-4 w-4 mr-2" /> : null}
                Adjust Stock
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Update Stock from Alert Dialog */}
        <Dialog open={!!selectedAlert} onOpenChange={() => setSelectedAlert(null)}>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Restock Product</DialogTitle>
            </DialogHeader>
            {selectedAlert && (
              <div className="space-y-4">
                <div>
                  <p className="font-medium">{selectedAlert.product_name}</p>
                  <p className="text-sm text-muted-foreground">Current stock: {selectedAlert.current_stock}</p>
                  <p className="text-sm text-orange-400">Suggested: +{selectedAlert.quantity_needed} units</p>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">New Stock Quantity</label>
                  <Input type="number" value={newStock} onChange={(e) => setNewStock(parseInt(e.target.value) || 0)} min={0} />
                </div>
                <div className="flex gap-3">
                  <Button variant="outline" className="flex-1" onClick={() => setSelectedAlert(null)}>
                    Cancel
                  </Button>
                  <Button className="flex-1 bg-orange-500 hover:bg-orange-600" onClick={handleUpdateStockFromAlert} disabled={isSubmitting}>
                    {isSubmitting ? "Updating..." : "Update Stock"}
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
