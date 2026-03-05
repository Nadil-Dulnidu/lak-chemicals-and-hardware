"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { productActions, orderActions, salesActions, quotationActions } from "@/lib/actions";
import Link from "next/link";
import { Package, ShoppingBag, DollarSign, AlertTriangle, TrendingUp, FileText, ArrowRight, Clock, CheckCircle } from "lucide-react";

interface DashboardStats {
  totalProducts: number;
  pendingOrders: number;
  pendingQuotations: number;
  lowStockCount: number;
  totalRevenue: number;
  totalSales: number;
}

export default function AdminDashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [recentOrders, setRecentOrders] = useState<
    Array<{
      order_id: number;
      status: string;
      total_amount: number;
      order_date: string;
    }>
  >([]);

  const [authToken, setAuthToken] = useState<string | null>(null);
  const { getToken } = useAuth();
  useEffect(() => {
    const fetchToken = async () => {
      const token = await getToken({ template: "lak-chemicles-and-hardware" });
      setAuthToken(token);
    };
    fetchToken();
  }, [getToken]);

  useEffect(() => {
    const fetchStats = async () => {
      if (!authToken) return;
      try {
        const [products, orders, quotations, lowStock, salesSummary] = await Promise.all([
          productActions.getAll(),
          orderActions.getAll(0, 5, authToken),
          quotationActions.getAll(0, 100, authToken),
          productActions.getLowStockAlerts(10, 100, authToken),
          salesActions.getSummary({}, authToken),
        ]);

        const pendingOrders = orders.orders.filter((o) => o.status === "PENDING").length;
        const pendingQuotations = quotations.quotations.filter((q) => q.status === "PENDING").length;

        setStats({
          totalProducts: products.total,
          pendingOrders,
          pendingQuotations,
          lowStockCount: lowStock.length,
          totalRevenue: salesSummary.total_revenue || 0,
          totalSales: salesSummary.total_sales || 0,
        });

        setRecentOrders(orders.orders.slice(0, 5));
      } catch (error) {
        console.error("Failed to fetch stats:", error);
      } finally {
        setIsLoading(false);
      }
    };

    if (authToken !== null) {
      fetchStats();
    }
  }, [authToken]);

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex justify-center items-center min-h-[60vh]">
          <Spinner className="h-8 w-8" />
        </div>
      </AdminLayout>
    );
  }

  const statCards = [
    {
      title: "Total Products",
      value: stats?.totalProducts || 0,
      icon: Package,
      color: "text-blue-400",
      bgColor: "bg-blue-500/10",
    },
    {
      title: "Pending Orders",
      value: stats?.pendingOrders || 0,
      icon: ShoppingBag,
      color: "text-yellow-400",
      bgColor: "bg-yellow-500/10",
    },
    {
      title: "Pending Quotations",
      value: stats?.pendingQuotations || 0,
      icon: FileText,
      color: "text-purple-400",
      bgColor: "bg-purple-500/10",
    },
    {
      title: "Low Stock Items",
      value: stats?.lowStockCount || 0,
      icon: AlertTriangle,
      color: "text-red-400",
      bgColor: "bg-red-500/10",
    },
    {
      title: "Total Revenue",
      value: `LKR ${(stats?.totalRevenue || 0).toLocaleString()}`,
      icon: DollarSign,
      color: "text-green-400",
      bgColor: "bg-green-500/10",
    },
    {
      title: "Total Sales",
      value: stats?.totalSales || 0,
      icon: TrendingUp,
      color: "text-orange-400",
      bgColor: "bg-orange-500/10",
    },
  ];

  return (
    <AdminLayout>
      <div className="space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold mb-2">Dashboard</h1>
          <p className="text-muted-foreground">Welcome back! Here&apos;s what&apos;s happening today.</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {statCards.map((stat) => {
            const Icon = stat.icon;
            return (
              <Card key={stat.title} className="bg-card/50 border-border/50">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-muted-foreground mb-1">{stat.title}</p>
                      <p className="text-2xl font-bold">{stat.value}</p>
                    </div>
                    <div className={`p-3 rounded-xl ${stat.bgColor}`}>
                      <Icon className={`h-6 w-6 ${stat.color}`} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Recent Orders */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Recent Orders</CardTitle>
              <Link href="/admin/orders">
                <Button variant="ghost" size="sm" className="gap-2 text-orange-400">
                  View All <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
            </CardHeader>
            <CardContent>
              {recentOrders.length > 0 ? (
                <div className="space-y-4">
                  {recentOrders.map((order) => (
                    <div key={order.order_id} className="flex items-center justify-between p-3 rounded-lg bg-muted/30">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-orange-500/10">
                          <ShoppingBag className="h-4 w-4 text-orange-400" />
                        </div>
                        <div>
                          <p className="font-medium">Order #{order.order_id}</p>
                          <p className="text-sm text-muted-foreground">{new Date(order.order_date).toLocaleDateString()}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">LKR {order.total_amount.toLocaleString()}</p>
                        <Badge
                          variant="outline"
                          className={
                            order.status === "PENDING"
                              ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/30"
                              : order.status === "COMPLETED"
                                ? "bg-green-500/10 text-green-400 border-green-500/30"
                                : "bg-red-500/10 text-red-400 border-red-500/30"
                          }
                        >
                          {order.status === "PENDING" && <Clock className="h-3 w-3 mr-1" />}
                          {order.status === "COMPLETED" && <CheckCircle className="h-3 w-3 mr-1" />}
                          {order.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">No recent orders</p>
              )}
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader>
              <CardTitle className="text-lg">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="grid grid-cols-2 gap-4">
              <Link href="/admin/products">
                <Button variant="outline" className="w-full h-auto py-6 flex flex-col gap-2">
                  <Package className="h-6 w-6 text-blue-400" />
                  <span>Manage Products</span>
                </Button>
              </Link>
              <Link href="/admin/orders">
                <Button variant="outline" className="w-full h-auto py-6 flex flex-col gap-2">
                  <ShoppingBag className="h-6 w-6 text-yellow-400" />
                  <span>View Orders</span>
                </Button>
              </Link>
              <Link href="/admin/quotations">
                <Button variant="outline" className="w-full h-auto py-6 flex flex-col gap-2">
                  <FileText className="h-6 w-6 text-purple-400" />
                  <span>Quotations</span>
                </Button>
              </Link>
              <Link href="/admin/reports">
                <Button variant="outline" className="w-full h-auto py-6 flex flex-col gap-2">
                  <TrendingUp className="h-6 w-6 text-green-400" />
                  <span>Reports</span>
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </div>
    </AdminLayout>
  );
}
