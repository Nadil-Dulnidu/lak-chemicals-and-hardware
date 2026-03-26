"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { orderActions } from "@/lib/actions";
import { Order } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { Clock, CheckCircle, XCircle, Eye, Filter, ShoppingCart, FileText, Package, Trash2, Truck, ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

const statusConfig = {
  PENDING: { icon: Clock, color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30", label: "Pending" },
  SHIPPED: { icon: Truck, color: "bg-blue-500/10 text-blue-400 border-blue-500/30", label: "Shipped" },
  DELIVERED: { icon: CheckCircle, color: "bg-green-500/10 text-green-400 border-green-500/30", label: "Delivered" },
  CANCELLED: { icon: XCircle, color: "bg-red-500/10 text-red-400 border-red-500/30", label: "Cancelled" },
};

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedOrder, setSelectedOrder] = useState<Order | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const [authToken, setAuthToken] = useState<string | null>(null);
  const { getToken } = useAuth();
  useEffect(() => {
    const fetchToken = async () => {
      const token = await getToken({ template: "lak-chemicles-and-hardware" });
      setAuthToken(token);
    };
    fetchToken();
  }, [getToken]);

  const fetchOrders = useCallback(async () => {
    if (!authToken) return;
    try {
      const response = await orderActions.getAll(0, 500, authToken);
      setOrders(response.orders);
    } catch {
      toast.error("Failed to fetch orders");
    } finally {
      setIsLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const updateOrderStatus = async (orderId: number, status: "PENDING" | "SHIPPED" | "CANCELLED" | "DELIVERED") => {
    setUpdatingId(orderId);
    try {
      await orderActions.updateStatus(orderId, status, authToken);
      const statusMessages: Record<string, string> = {
        SHIPPED: "Order marked as shipped",
        DELIVERED: "Order marked as delivered",
        CANCELLED: "Order cancelled",
        PENDING: "Order set back to pending",
      };
      toast.success(statusMessages[status] || "Order updated");
      fetchOrders();
      // Refresh selectedOrder if the detail dialog is open for this order
      if (selectedOrder?.order_id === orderId) {
        const updatedOrders = await orderActions.getAll(0, 500, authToken);
        const updated = updatedOrders.orders.find((o) => o.order_id === orderId);
        if (updated) setSelectedOrder(updated);
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update order");
    } finally {
      setUpdatingId(null);
    }
  };

  const deleteOrder = async (orderId: number) => {
    if (!confirm("Are you sure you want to delete this cancelled order?")) return;
    setDeletingId(orderId);
    try {
      await orderActions.delete(orderId, authToken);
      toast.success("Order deleted successfully");
      fetchOrders();
      if (selectedOrder?.order_id === orderId) setSelectedOrder(null);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to delete order");
    } finally {
      setDeletingId(null);
    }
  };

  const filteredOrders = orders.filter((order) => statusFilter === "all" || order.status === statusFilter);

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
            <h1 className="text-3xl font-bold mb-2">Orders</h1>
            <p className="text-muted-foreground">Manage customer orders</p>
          </div>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Filter className="h-4 w-4 text-muted-foreground" />
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40 bg-card/50 border-border/50">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Orders</SelectItem>
                  <SelectItem value="PENDING">Pending</SelectItem>
                  <SelectItem value="SHIPPED">Shipped</SelectItem>
                  <SelectItem value="DELIVERED">Delivered</SelectItem>
                  <SelectItem value="CANCELLED">Cancelled</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {(["PENDING", "SHIPPED", "DELIVERED", "CANCELLED"] as const).map((status) => {
            const count = orders.filter((o) => o.status === status).length;
            const Icon = statusConfig[status].icon;
            return (
              <Card key={status} className="bg-card/50 border-border/50">
                <CardContent className="p-4 flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{statusConfig[status].label}</p>
                    <p className="text-2xl font-bold">{count}</p>
                  </div>
                  <div className={cn("p-3 rounded-xl", statusConfig[status].color.split(" ")[0])}>
                    <Icon className={cn("h-5 w-5", statusConfig[status].color.split(" ")[1])} />
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Orders Table */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left p-4 font-medium text-muted-foreground">Order ID</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Customer</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Date</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Source</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Items</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Total</th>
                    <th className="text-center p-4 font-medium text-muted-foreground">Status</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredOrders.map((order) => {
                    const StatusIcon = statusConfig[order.status].icon;
                    return (
                      <tr key={order.order_id} className="border-b border-border/50 hover:bg-muted/30">
                        <td className="p-4">
                          <span className="font-medium">#{order.order_id}</span>
                        </td>
                        <td className="p-4 text-muted-foreground">{order.user_id}</td>
                        <td className="p-4 text-muted-foreground">{new Date(order.order_date).toLocaleDateString()}</td>
                        <td className="p-4">
                          <Badge variant="outline" className="text-xs">
                            {order.cart_id ? (
                              <>
                                <ShoppingCart className="h-3 w-3 mr-1 inline" />
                                Cart
                              </>
                            ) : order.quotation_id ? (
                              <>
                                <FileText className="h-3 w-3 mr-1 inline" />
                                Quotation
                              </>
                            ) : (
                              "Direct"
                            )}
                          </Badge>
                        </td>
                        <td className="p-4 text-right">{order.items.length}</td>
                        <td className="p-4 text-right font-medium">LKR {order.total_amount.toLocaleString()}</td>
                        <td className="p-4 text-center">
                          <Badge className={cn("border", statusConfig[order.status].color)}>
                            <StatusIcon className="h-3 w-3 mr-1" />
                            {statusConfig[order.status].label}
                          </Badge>
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button variant="ghost" size="sm" onClick={() => setSelectedOrder(order)}>
                              <Eye className="h-4 w-4" />
                            </Button>

                            {/* Status Dropdown — shown for PENDING & SHIPPED orders */}
                            {(order.status === "PENDING" || order.status === "SHIPPED") && (
                              <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                  <Button
                                    variant="outline"
                                    size="sm"
                                    className="gap-1 border-border/50"
                                    disabled={updatingId === order.order_id}
                                  >
                                    {updatingId === order.order_id ? (
                                      <Spinner className="h-3 w-3" />
                                    ) : (
                                      <>
                                        Update
                                        <ChevronDown className="h-3 w-3" />
                                      </>
                                    )}
                                  </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                  <DropdownMenuLabel>Change Status</DropdownMenuLabel>
                                  <DropdownMenuSeparator />
                                  {order.status === "PENDING" && (
                                    <>
                                      <DropdownMenuItem
                                        onClick={() => updateOrderStatus(order.order_id, "SHIPPED")}
                                        className="gap-2 text-blue-400 focus:text-blue-400"
                                      >
                                        <Truck className="h-4 w-4" />
                                        Mark as Shipped
                                      </DropdownMenuItem>
                                      <DropdownMenuSeparator />
                                      <DropdownMenuItem
                                        onClick={() => updateOrderStatus(order.order_id, "CANCELLED")}
                                        className="gap-2 text-red-400 focus:text-red-400"
                                      >
                                        <XCircle className="h-4 w-4" />
                                        Cancel Order
                                      </DropdownMenuItem>
                                    </>
                                  )}
                                  {order.status === "SHIPPED" && (
                                    <>
                                      <DropdownMenuItem
                                        onClick={() => updateOrderStatus(order.order_id, "DELIVERED")}
                                        className="gap-2 text-green-400 focus:text-green-400"
                                      >
                                        <CheckCircle className="h-4 w-4" />
                                        Mark as Delivered
                                      </DropdownMenuItem>
                                      <DropdownMenuSeparator />
                                      <DropdownMenuItem
                                        onClick={() => updateOrderStatus(order.order_id, "CANCELLED")}
                                        className="gap-2 text-red-400 focus:text-red-400"
                                      >
                                        <XCircle className="h-4 w-4" />
                                        Cancel Order
                                      </DropdownMenuItem>
                                    </>
                                  )}
                                </DropdownMenuContent>
                              </DropdownMenu>
                            )}

                            {order.status === "CANCELLED" && (
                              <Button
                                variant="outline"
                                size="sm"
                                className="text-red-400 border-red-500/30 hover:bg-red-500/10"
                                onClick={() => deleteOrder(order.order_id)}
                                disabled={deletingId === order.order_id}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {filteredOrders.length === 0 && <div className="py-12 text-center text-muted-foreground">No orders found</div>}
          </CardContent>
        </Card>

        {/* Order Detail Dialog */}
        <Dialog open={!!selectedOrder} onOpenChange={() => setSelectedOrder(null)}>
          <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Order #{selectedOrder?.order_id}</DialogTitle>
            </DialogHeader>
            {selectedOrder && (
              <div className="space-y-4">
                {/* Status & Date */}
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Status</span>
                  <Badge className={cn("border", statusConfig[selectedOrder.status].color)}>{statusConfig[selectedOrder.status].label}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Date</span>
                  <span>{new Date(selectedOrder.order_date).toLocaleString()}</span>
                </div>

                <Separator />

                {/* Customer Information Section */}
                <div className="space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <span className="text-orange-400">👤</span>
                    Customer Information
                  </h4>
                  <div className="bg-muted/30 rounded-lg p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground text-sm">Name</span>
                      <span className="font-medium">{selectedOrder.customer_name || "Not provided"}</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground text-sm">Phone</span>
                      <span className="font-medium">
                        {selectedOrder.phone ? (
                          <a href={`tel:${selectedOrder.phone}`} className="text-orange-400 hover:underline">
                            {selectedOrder.phone}
                          </a>
                        ) : (
                          "Not provided"
                        )}
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground text-sm">Address</span>
                      <span className="font-medium text-right max-w-[200px]">{selectedOrder.address || "Not provided"}</span>
                    </div>
                    {selectedOrder.city && (
                      <div className="flex items-center justify-between">
                        <span className="text-muted-foreground text-sm">City</span>
                        <span className="font-medium">{selectedOrder.city}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Payment & Notes Section */}
                {(selectedOrder.payment_method || selectedOrder.notes) && (
                  <>
                    <Separator />
                    <div className="space-y-3">
                      <h4 className="font-medium flex items-center gap-2">
                        <span className="text-orange-400">💳</span>
                        Payment & Notes
                      </h4>
                      <div className="bg-muted/30 rounded-lg p-4 space-y-2">
                        {selectedOrder.payment_method && (
                          <div className="flex items-center justify-between">
                            <span className="text-muted-foreground text-sm">Payment Method</span>
                            <span className="font-medium">{selectedOrder.payment_method}</span>
                          </div>
                        )}
                        {selectedOrder.notes && (
                          <div>
                            <span className="text-muted-foreground text-sm block mb-1">Notes</span>
                            <p className="text-sm bg-background/50 rounded p-2">{selectedOrder.notes}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                )}

                <Separator />

                {/* Order Source */}
                <div className="space-y-3">
                  <h4 className="font-medium flex items-center gap-2">
                    <span className="text-orange-400">📦</span>
                    Order Source
                  </h4>
                  <div className="bg-muted/30 rounded-lg p-4 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground text-sm">Source</span>
                      <Badge variant="outline">{selectedOrder.cart_id ? `Cart #${selectedOrder.cart_id}` : selectedOrder.quotation_id ? `Quotation #${selectedOrder.quotation_id}` : "Direct"}</Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-muted-foreground text-sm">Payment Status</span>
                      <Badge className={selectedOrder.payment_status === "PAID" ? "bg-green-500/10 text-green-400 border-green-500/30" : "bg-yellow-500/10 text-yellow-400 border-yellow-500/30"}>
                        {selectedOrder.payment_status}
                      </Badge>
                    </div>
                  </div>
                </div>

                <Separator />

                {/* Order Items */}
                {selectedOrder.items.length > 0 && (
                  <div className="space-y-3">
                    <h4 className="font-medium flex items-center gap-2">
                      <span className="text-orange-400">📦</span>
                      Items ({selectedOrder.items.length})
                    </h4>
                    {selectedOrder.items.map((item) => (
                      <div key={item.id} className="flex items-center justify-between py-2">
                        <div className="flex items-center gap-3">
                          <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                            <Package className="h-5 w-5 text-muted-foreground/50" />
                          </div>
                          <div>
                            <p className="font-medium">{item.product_name}</p>
                            <p className="text-sm text-muted-foreground">
                              {item.quantity} × LKR {item.unit_price.toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <p className="font-medium">LKR {item.subtotal.toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                )}

                <Separator />

                {/* Total */}
                <div className="flex items-center justify-between font-bold text-lg">
                  <span>Total</span>
                  <span className="text-orange-400">LKR {selectedOrder.total_amount.toLocaleString()}</span>
                </div>

                {/* Action Buttons — Dropdown for status changes */}
                {(selectedOrder.status === "PENDING" || selectedOrder.status === "SHIPPED") && (
                  <div className="flex gap-3 pt-4">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button className="flex-1 bg-orange-500 hover:bg-orange-600" disabled={updatingId === selectedOrder.order_id}>
                          {updatingId === selectedOrder.order_id ? (
                            <Spinner className="h-4 w-4 mr-2" />
                          ) : (
                            <ChevronDown className="h-4 w-4 mr-2" />
                          )}
                          Update Status
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="center" className="w-56">
                        <DropdownMenuLabel>Change Order Status</DropdownMenuLabel>
                        <DropdownMenuSeparator />
                        {selectedOrder.status === "PENDING" && (
                          <>
                            <DropdownMenuItem
                              onClick={() => updateOrderStatus(selectedOrder.order_id, "SHIPPED")}
                              className="gap-2 text-blue-400 focus:text-blue-400"
                            >
                              <Truck className="h-4 w-4" />
                              Mark as Shipped
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => updateOrderStatus(selectedOrder.order_id, "CANCELLED")}
                              className="gap-2 text-red-400 focus:text-red-400"
                            >
                              <XCircle className="h-4 w-4" />
                              Cancel Order
                            </DropdownMenuItem>
                          </>
                        )}
                        {selectedOrder.status === "SHIPPED" && (
                          <>
                            <DropdownMenuItem
                              onClick={() => updateOrderStatus(selectedOrder.order_id, "DELIVERED")}
                              className="gap-2 text-green-400 focus:text-green-400"
                            >
                              <CheckCircle className="h-4 w-4" />
                              Mark as Delivered
                            </DropdownMenuItem>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem
                              onClick={() => updateOrderStatus(selectedOrder.order_id, "CANCELLED")}
                              className="gap-2 text-red-400 focus:text-red-400"
                            >
                              <XCircle className="h-4 w-4" />
                              Cancel Order
                            </DropdownMenuItem>
                          </>
                        )}
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                )}
                {selectedOrder.status === "CANCELLED" && (
                  <div className="pt-4">
                    <Button variant="destructive" className="w-full" onClick={() => deleteOrder(selectedOrder.order_id)} disabled={deletingId === selectedOrder.order_id}>
                      <Trash2 className="h-4 w-4 mr-2" />
                      Delete Cancelled Order
                    </Button>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>
      </div>
    </AdminLayout>
  );
}
