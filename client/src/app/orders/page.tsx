"use client";

import { useEffect, useState, useCallback } from "react";
import { CustomerLayout } from "@/components/layouts/customer-layout";
import { orderActions } from "@/lib/actions";
import { Order } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import Link from "next/link";
import { ClipboardList, Clock, CheckCircle, XCircle, ArrowRight, ChevronDown, ChevronUp, Package, Truck, AlertTriangle, CreditCard, Banknote } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth, useUser } from "@clerk/nextjs";

const statusConfig = {
  PENDING: { icon: Clock, color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30", label: "Processing" },
  COMPLETED: { icon: CheckCircle, color: "bg-green-500/10 text-green-400 border-green-500/30", label: "Completed" },
  DELIVERED: { icon: Truck, color: "bg-blue-500/10 text-blue-400 border-blue-500/30", label: "Delivered" },
  CANCELLED: { icon: XCircle, color: "bg-red-500/10 text-red-400 border-red-500/30", label: "Cancelled" },
};

/**
 * Safely parse a potentially naive backend datetime string as UTC
 */
function parseUTCDate(dateString: string): number {
  if (!dateString) return 0;
  // If the string doesn't end with Z and doesn't have a + or - offset, append Z to force UTC parsing
  const isNaive = !dateString.endsWith('Z') && !dateString.match(/[+\-]\d{2}:\d{2}$/);
  const safeString = isNaive ? `${dateString}Z` : dateString;
  return new Date(safeString).getTime();
}

/**
 * Check if an order is eligible for cancellation (within 1 hour of placement)
 */
function canCancelOrder(order: Order): boolean {
  if (order.status !== "PENDING") return false;
  const orderTime = parseUTCDate(order.order_date);
  const now = Date.now();
  const oneHourMs = 60 * 60 * 1000;
  return now - orderTime < oneHourMs && now >= orderTime;
}

/**
 * Get remaining minutes for cancellation window
 */
function getCancelMinutesLeft(order: Order): number {
  const orderTime = parseUTCDate(order.order_date);
  const now = Date.now();
  const oneHourMs = 60 * 60 * 1000;
  const remaining = oneHourMs - (now - orderTime);
  return Math.max(0, Math.ceil(remaining / 60000));
}

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [cancelDialogOrder, setCancelDialogOrder] = useState<Order | null>(null);
  const [cancellingId, setCancellingId] = useState<number | null>(null);
  const [cancelSuccessOrder, setCancelSuccessOrder] = useState<Order | null>(null);

  const [authToken, setAuthToken] = useState<string | null>(null);
  const { getToken } = useAuth();
  const { user } = useUser();

  // Force re-render every 30 seconds to update the live countdown timers
  const [, setTick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setTick((t) => t + 1), 30000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const fetchToken = async () => {
      const token = await getToken({ template: "lak-chemicles-and-hardware" });
      setAuthToken(token);
    };
    fetchToken();
  }, [getToken]);

  const fetchOrders = useCallback(async () => {
    if (!authToken || !user?.id) return;
    try {
      const userId = user?.id;
      const response = await orderActions.getByUserId(userId, 0, 100, authToken);
      setOrders(response.orders);
    } catch {
      toast.error("Failed to load orders");
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, authToken]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

  const handleCancelOrder = async () => {
    if (!cancelDialogOrder) return;
    setCancellingId(cancelDialogOrder.order_id);
    try {
      await orderActions.updateStatus(cancelDialogOrder.order_id, "CANCELLED", authToken);
      // Store the order info before refreshing so we can show the success dialog
      setCancelSuccessOrder(cancelDialogOrder);
      setCancelDialogOrder(null);
      fetchOrders();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to cancel order");
    } finally {
      setCancellingId(null);
    }
  };

  if (isLoading) {
    return (
      <CustomerLayout>
        <div className="container mx-auto px-4 py-8 flex justify-center items-center min-h-[60vh]">
          <Spinner className="h-8 w-8" />
        </div>
      </CustomerLayout>
    );
  }

  if (orders.length === 0) {
    return (
      <CustomerLayout>
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
            <ClipboardList className="h-20 w-20 text-muted-foreground/30 mb-6" />
            <h1 className="text-2xl font-bold mb-2">No orders yet</h1>
            <p className="text-muted-foreground mb-6">Start shopping to place your first order</p>
            <Link href="/products">
              <Button className="gap-2 bg-orange-500 hover:bg-orange-600">
                Browse Products
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </CustomerLayout>
    );
  }

  return (
    <CustomerLayout>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">My Orders</h1>
          <p className="text-muted-foreground">Track and view your order history</p>
        </div>

        {/* Orders List */}
        <div className="space-y-4">
          {orders.map((order) => {
            const StatusIcon = statusConfig[order.status].icon;
            const isExpanded = expandedId === order.order_id;
            const cancellable = canCancelOrder(order);
            const minutesLeft = cancellable ? getCancelMinutesLeft(order) : 0;

            return (
              <Card key={order.order_id} className="bg-card/50 border-border/50">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <CardTitle className="text-lg">Order #{order.order_id}</CardTitle>
                      <Badge className={cn("border", statusConfig[order.status].color)}>
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {statusConfig[order.status].label}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold">LKR {order.total_amount.toLocaleString()}</span>
                      <Button variant="ghost" size="icon" onClick={() => setExpandedId(isExpanded ? null : order.order_id)}>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <p className="text-sm text-muted-foreground">
                      Ordered on {new Date(order.order_date).toLocaleDateString()}
                      {order.payment_method && ` • ${order.payment_method}`}
                    </p>
                    {/* Cancel button shown inline for eligible orders */}
                    {cancellable && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="text-red-400 border-red-500/30 hover:bg-red-500/10 gap-1.5"
                        onClick={() => setCancelDialogOrder(order)}
                      >
                        <XCircle className="h-3.5 w-3.5" />
                        Cancel ({minutesLeft}m left)
                      </Button>
                    )}
                  </div>
                </CardHeader>

                {isExpanded && (
                  <CardContent>
                    <Separator className="mb-4" />

                    {/* Order Timeline — now includes Delivered step */}
                    <div className="mb-6 p-4 rounded-lg bg-muted/30">
                      <h4 className="font-medium mb-3">Order Status</h4>
                      <div className="flex items-center gap-2 sm:gap-4">
                        {/* Order Placed */}
                        <div className="flex items-center gap-1.5">
                          <div className="h-3 w-3 rounded-full bg-green-500" />
                          <span className="text-xs sm:text-sm">Placed</span>
                        </div>
                        <div className="h-px flex-1 bg-border" />

                        {/* Processing */}
                        <div className="flex items-center gap-1.5">
                          <div className={cn("h-3 w-3 rounded-full", order.status !== "CANCELLED" ? "bg-green-500" : "bg-muted")} />
                          <span className="text-xs sm:text-sm">Processing</span>
                        </div>
                        <div className="h-px flex-1 bg-border" />

                        {/* Completed */}
                        <div className="flex items-center gap-1.5">
                          <div className={cn("h-3 w-3 rounded-full", order.status === "COMPLETED" || order.status === "DELIVERED" ? "bg-green-500" : "bg-muted")} />
                          <span className="text-xs sm:text-sm">Completed</span>
                        </div>
                        <div className="h-px flex-1 bg-border" />

                        {/* Delivered */}
                        <div className="flex items-center gap-1.5">
                          <div className={cn("h-3 w-3 rounded-full", order.status === "DELIVERED" ? "bg-blue-500" : "bg-muted")} />
                          <span className="text-xs sm:text-sm">Delivered</span>
                        </div>
                      </div>

                      {/* Cancelled banner */}
                      {order.status === "CANCELLED" && (
                        <div className="mt-3 p-2 rounded-md bg-red-500/10 border border-red-500/20 flex items-center gap-2">
                          <XCircle className="h-4 w-4 text-red-400 shrink-0" />
                          <span className="text-sm text-red-400">This order has been cancelled</span>
                        </div>
                      )}

                      {/* Delivered banner */}
                      {order.status === "DELIVERED" && (
                        <div className="mt-3 p-2 rounded-md bg-blue-500/10 border border-blue-500/20 flex items-center gap-2">
                          <Truck className="h-4 w-4 text-blue-400 shrink-0" />
                          <span className="text-sm text-blue-400">Your order has been delivered successfully!</span>
                        </div>
                      )}
                    </div>

                    {/* Order Source */}
                    <div className="mb-6 p-4 rounded-lg bg-muted/30">
                      <h4 className="font-medium mb-3">Order Details</h4>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Source</span>
                          <Badge variant="outline">{order.cart_id ? `From Cart #${order.cart_id}` : order.quotation_id ? `From Quotation #${order.quotation_id}` : "Direct"}</Badge>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Payment</span>
                          <span>{order.payment_method || "Not specified"}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-muted-foreground">Payment Status</span>
                          <Badge className={order.payment_status === "PAID" ? "bg-green-500/10 text-green-400 border-green-500/30" : "bg-yellow-500/10 text-yellow-400 border-yellow-500/30"}>
                            {order.payment_status}
                          </Badge>
                        </div>
                        {order.customer_name && (
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Customer</span>
                            <span>{order.customer_name}</span>
                          </div>
                        )}
                        {order.address && (
                          <div className="flex justify-between text-sm">
                            <span className="text-muted-foreground">Address</span>
                            <span className="text-right max-w-[200px]">
                              {order.address}
                              {order.city ? `, ${order.city}` : ""}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Order Items */}
                    {order.items.length > 0 && (
                      <div className="mb-6">
                        <h4 className="font-medium mb-3">Order Items</h4>
                        <div className="space-y-3">
                          {order.items.map((item) => (
                            <div key={item.id} className="flex items-center justify-between py-2">
                              <div className="flex items-center gap-3">
                                <div className="h-12 w-12 rounded-lg bg-muted flex items-center justify-center">
                                  <Package className="h-5 w-5 text-muted-foreground/50" />
                                </div>
                                <div>
                                  <p className="font-medium">{item.product_name}</p>
                                  <p className="text-sm text-muted-foreground">
                                    Qty: {item.quantity} × LKR {item.unit_price.toLocaleString()}
                                  </p>
                                </div>
                              </div>
                              <p className="font-semibold">LKR {item.subtotal.toLocaleString()}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Summary */}
                    <div className="p-4 rounded-lg bg-muted/30">
                      <div className="flex justify-between font-bold">
                        <span>Total</span>
                        <span>LKR {order.total_amount.toLocaleString()}</span>
                      </div>
                    </div>

                    {/* Cancel button at bottom for expanded view */}
                    {cancellable && (
                      <div className="mt-4">
                        <Button
                          variant="outline"
                          className="w-full text-red-400 border-red-500/30 hover:bg-red-500/10 gap-2"
                          onClick={() => setCancelDialogOrder(order)}
                        >
                          <XCircle className="h-4 w-4" />
                          Cancel This Order ({minutesLeft}m remaining)
                        </Button>
                      </div>
                    )}
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      </div>

      {/* Cancel Confirmation Dialog */}
      <Dialog open={!!cancelDialogOrder} onOpenChange={() => setCancelDialogOrder(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-3 rounded-full bg-red-500/10">
                <AlertTriangle className="h-6 w-6 text-red-400" />
              </div>
              <DialogTitle className="text-xl">Cancel Order #{cancelDialogOrder?.order_id}?</DialogTitle>
            </div>
            <DialogDescription className="text-base">
              Are you sure you want to cancel this order? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>

          {cancelDialogOrder && (
            <div className="space-y-4">
              {/* Order summary */}
              <div className="p-4 rounded-lg bg-muted/30 space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Order Total</span>
                  <span className="font-bold">LKR {cancelDialogOrder.total_amount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Payment Method</span>
                  <span className="font-medium">{cancelDialogOrder.payment_method || "Cash"}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Items</span>
                  <span>{cancelDialogOrder.items.length} item(s)</span>
                </div>
              </div>

              {/* Refund message based on payment method */}
              {cancelDialogOrder.payment_method?.toLowerCase() === "card" && cancelDialogOrder.payment_status === "PAID" ? (
                <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20 flex gap-3">
                  <CreditCard className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-400 mb-1">Card Payment Refund</p>
                    <p className="text-sm text-muted-foreground">
                      Since you paid by card, your refund of <strong className="text-foreground">LKR {cancelDialogOrder.total_amount.toLocaleString()}</strong> will be processed back to your original payment method. This may take <strong className="text-foreground">5–10 business days</strong> to reflect in your account.
                    </p>
                  </div>
                </div>
              ) : cancelDialogOrder.payment_status === "PAID" ? (
                <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20 flex gap-3">
                  <Banknote className="h-5 w-5 text-green-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-green-400 mb-1">Cash Payment Refund</p>
                    <p className="text-sm text-muted-foreground">
                      Since you paid by cash, your refund of <strong className="text-foreground">LKR {cancelDialogOrder.total_amount.toLocaleString()}</strong> will be arranged. Our team will contact you shortly to process the refund.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20 flex gap-3">
                  <AlertTriangle className="h-5 w-5 text-yellow-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-yellow-400 mb-1">No Payment Made</p>
                    <p className="text-sm text-muted-foreground">
                      No payment has been processed for this order yet. The order will simply be cancelled with no charges.
                    </p>
                  </div>
                </div>
              )}

              {/* Time remaining */}
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>
                  You have <strong className="text-foreground">{getCancelMinutesLeft(cancelDialogOrder)} minutes</strong> left to cancel this order
                </span>
              </div>
            </div>
          )}

          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="outline" onClick={() => setCancelDialogOrder(null)}>
              Keep Order
            </Button>
            <Button
              variant="destructive"
              onClick={handleCancelOrder}
              disabled={cancellingId !== null}
              className="gap-2"
            >
              {cancellingId !== null ? (
                <Spinner className="h-4 w-4" />
              ) : (
                <XCircle className="h-4 w-4" />
              )}
              Yes, Cancel Order
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cancellation Success Dialog */}
      <Dialog open={!!cancelSuccessOrder} onOpenChange={() => setCancelSuccessOrder(null)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <div className="flex items-center gap-3 mb-2">
              <div className="p-3 rounded-full bg-green-500/10">
                <CheckCircle className="h-6 w-6 text-green-400" />
              </div>
              <DialogTitle className="text-xl">Order Cancelled</DialogTitle>
            </div>
            <DialogDescription className="text-base">
              Order #{cancelSuccessOrder?.order_id} has been cancelled successfully.
            </DialogDescription>
          </DialogHeader>

          {cancelSuccessOrder && (
            <div className="space-y-4">
              {/* Refund info */}
              {cancelSuccessOrder.payment_method?.toLowerCase() === "card" && cancelSuccessOrder.payment_status === "PAID" ? (
                <div className="p-4 rounded-lg bg-blue-500/10 border border-blue-500/20 flex gap-3">
                  <CreditCard className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-blue-400 mb-1">Refund In Progress</p>
                    <p className="text-sm text-muted-foreground">
                      Your refund of <strong className="text-foreground">LKR {cancelSuccessOrder.total_amount.toLocaleString()}</strong> is being processed. It will be credited back to your card within <strong className="text-foreground">5–10 business days</strong>.
                    </p>
                  </div>
                </div>
              ) : cancelSuccessOrder.payment_status === "PAID" ? (
                <div className="p-4 rounded-lg bg-green-500/10 border border-green-500/20 flex gap-3">
                  <Banknote className="h-5 w-5 text-green-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm font-medium text-green-400 mb-1">Refund Arranged</p>
                    <p className="text-sm text-muted-foreground">
                      Our team will contact you to arrange the refund of <strong className="text-foreground">LKR {cancelSuccessOrder.total_amount.toLocaleString()}</strong>.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="p-4 rounded-lg bg-muted/30 border border-border/50 flex gap-3">
                  <CheckCircle className="h-5 w-5 text-green-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-sm text-muted-foreground">
                      No payment was processed, so no refund is needed. The order has been cancelled.
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}

          <DialogFooter>
            <Button className="w-full bg-orange-500 hover:bg-orange-600" onClick={() => setCancelSuccessOrder(null)}>
              Got it
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </CustomerLayout>
  );
}
