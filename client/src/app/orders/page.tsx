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
import { toast } from "sonner";
import Link from "next/link";
import { ClipboardList, Clock, CheckCircle, XCircle, ArrowRight, ChevronDown, ChevronUp, Package } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth, useUser } from "@clerk/nextjs";

const statusConfig = {
  PENDING: { icon: Clock, color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30", label: "Processing" },
  COMPLETED: { icon: CheckCircle, color: "bg-green-500/10 text-green-400 border-green-500/30", label: "Completed" },
  CANCELLED: { icon: XCircle, color: "bg-red-500/10 text-red-400 border-red-500/30", label: "Cancelled" },
};

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);

  const [authToken, setAuthToken] = useState<string | null>(null);
  const { getToken } = useAuth();
  const { user } = useUser();

  useEffect(() => {
    const fetchToken = async () => {
      const token = await getToken({ template: "lak-chemicles-and-hardware" });
      setAuthToken(token);
    };
    fetchToken();
  }, [getToken]);

  console.log("AUth Token:", authToken);

  const fetchOrders = useCallback(async () => {
    if (!authToken || !user?.id) return;
    try {
      const userId = user?.id;
      const response = await orderActions.getByUserId(userId, 0, 100, authToken);
      setOrders(response.orders);
    } catch (error) {
      toast.error("Failed to load orders");
    } finally {
      setIsLoading(false);
    }
  }, [user?.id, authToken]);

  useEffect(() => {
    fetchOrders();
  }, [fetchOrders]);

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
                  <p className="text-sm text-muted-foreground">
                    Ordered on {new Date(order.order_date).toLocaleDateString()}
                    {order.payment_method && ` • ${order.payment_method}`}
                  </p>
                </CardHeader>

                {isExpanded && (
                  <CardContent>
                    <Separator className="mb-4" />

                    {/* Order Timeline */}
                    <div className="mb-6 p-4 rounded-lg bg-muted/30">
                      <h4 className="font-medium mb-3">Order Status</h4>
                      <div className="flex items-center gap-4">
                        <div className="flex items-center gap-2">
                          <div className="h-3 w-3 rounded-full bg-green-500" />
                          <span className="text-sm">Order Placed</span>
                        </div>
                        <div className="h-px flex-1 bg-border" />
                        <div className="flex items-center gap-2">
                          <div className={cn("h-3 w-3 rounded-full", order.status !== "CANCELLED" ? "bg-green-500" : "bg-muted")} />
                          <span className="text-sm">Processing</span>
                        </div>
                        <div className="h-px flex-1 bg-border" />
                        <div className="flex items-center gap-2">
                          <div className={cn("h-3 w-3 rounded-full", order.status === "COMPLETED" ? "bg-green-500" : "bg-muted")} />
                          <span className="text-sm">Completed</span>
                        </div>
                      </div>
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
                  </CardContent>
                )}
              </Card>
            );
          })}
        </div>
      </div>
    </CustomerLayout>
  );
}
