"use client";

import { useEffect, useState, useCallback } from "react";
import { CustomerLayout } from "@/components/layouts/customer-layout";
import { quotationActions, orderActions } from "@/lib/actions";
import { Quotation } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import Link from "next/link";
import { FileText, Clock, CheckCircle, XCircle, ArrowRight, ShoppingBag, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth, useUser } from "@clerk/nextjs";

const statusConfig = {
  PENDING: { icon: Clock, color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30" },
  APPROVED: { icon: CheckCircle, color: "bg-green-500/10 text-green-400 border-green-500/30" },
  REJECTED: { icon: XCircle, color: "bg-red-500/10 text-red-400 border-red-500/30" },
};

export default function QuotationsPage() {
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [processingId, setProcessingId] = useState<number | null>(null);

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

  const fetchQuotations = useCallback(async () => {
    if (!authToken || !user) return;
    try {
      const response = await quotationActions.getByUserId(authToken, user.id);
      setQuotations(response.quotations);
    } catch (error) {
      toast.error("Failed to load quotations");
    } finally {
      setIsLoading(false);
    }
  }, [authToken, user]);

  useEffect(() => {
    fetchQuotations();
  }, [fetchQuotations]);

  const createOrderFromQuotation = async (quotationId: number) => {
    setProcessingId(quotationId);
    try {
      // await orderActions.createFromQuotation({ quotation_id: quotationId });
      toast.success("Order created successfully!");
      fetchQuotations();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to create order");
    } finally {
      setProcessingId(null);
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

  if (quotations.length === 0) {
    return (
      <CustomerLayout>
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
            <FileText className="h-20 w-20 text-muted-foreground/30 mb-6" />
            <h1 className="text-2xl font-bold mb-2">No quotations yet</h1>
            <p className="text-muted-foreground mb-6">Add products to your cart and request a quotation</p>
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
          <h1 className="text-3xl font-bold mb-2">My Quotations</h1>
          <p className="text-muted-foreground">View and manage your quotation requests</p>
        </div>

        {/* Quotations List */}
        <div className="space-y-4">
          {quotations.map((quotation) => {
            const StatusIcon = statusConfig[quotation.status].icon;
            const isExpanded = expandedId === quotation.quotation_id;

            return (
              <Card key={quotation.quotation_id} className="bg-card/50 border-border/50">
                <CardHeader className="pb-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <CardTitle className="text-lg">Quotation #{quotation.quotation_id}</CardTitle>
                      <Badge className={cn("border", statusConfig[quotation.status].color)}>
                        <StatusIcon className="h-3 w-3 mr-1" />
                        {quotation.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-lg font-bold">LKR {quotation.total_amount.toLocaleString()}</span>
                      <Button variant="ghost" size="icon" onClick={() => setExpandedId(isExpanded ? null : quotation.quotation_id)}>
                        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                      </Button>
                    </div>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Created on {new Date(quotation.created_at).toLocaleDateString()}
                    {quotation.notes && ` • ${quotation.notes}`}
                  </p>
                </CardHeader>

                {isExpanded && (
                  <CardContent>
                    <Separator className="mb-4" />

                    {/* Items */}
                    <div className="space-y-3 mb-6">
                      {quotation.items.map((item) => (
                        <div key={item.quotation_item_id} className="flex items-center justify-between py-2">
                          <div>
                            <p className="font-medium">{item.product_name}</p>
                            <p className="text-sm text-muted-foreground">
                              Qty: {item.quantity} × LKR {item.unit_price.toLocaleString()}
                            </p>
                          </div>
                          <p className="font-semibold">LKR {item.subtotal.toLocaleString()}</p>
                        </div>
                      ))}
                    </div>

                    {/* Actions */}
                    {quotation.status === "APPROVED" && (
                      <Button
                        className="w-full gap-2 bg-orange-500 hover:bg-orange-600"
                        onClick={() => createOrderFromQuotation(quotation.quotation_id)}
                        disabled={processingId === quotation.quotation_id}
                      >
                        <ShoppingBag className="h-4 w-4" />
                        {processingId === quotation.quotation_id ? "Creating Order..." : "Place Order"}
                      </Button>
                    )}
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
