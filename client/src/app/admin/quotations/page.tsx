"use client";

import { useEffect, useState, useCallback } from "react";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { quotationActions } from "@/lib/actions";
import { Quotation } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Clock, CheckCircle, XCircle, Eye, Package, Filter } from "lucide-react";
import { cn } from "@/lib/utils";

const statusConfig = {
  PENDING: { icon: Clock, color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30", label: "Pending" },
  APPROVED: { icon: CheckCircle, color: "bg-green-500/10 text-green-400 border-green-500/30", label: "Approved" },
  REJECTED: { icon: XCircle, color: "bg-red-500/10 text-red-400 border-red-500/30", label: "Rejected" },
};

export default function AdminQuotationsPage() {
  const [quotations, setQuotations] = useState<Quotation[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [selectedQuotation, setSelectedQuotation] = useState<Quotation | null>(null);
  const [updatingId, setUpdatingId] = useState<number | null>(null);

  const fetchQuotations = useCallback(async () => {
    try {
      const response = await quotationActions.getAll(0, 500);
      setQuotations(response.quotations);
    } catch (error) {
      toast.error("Failed to fetch quotations");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchQuotations();
  }, [fetchQuotations]);

  const updateQuotationStatus = async (quotationId: number, status: "APPROVED" | "REJECTED") => {
    setUpdatingId(quotationId);
    try {
      await quotationActions.updateStatus(quotationId, status);
      toast.success(`Quotation ${status.toLowerCase()}`);
      fetchQuotations();
      setSelectedQuotation(null);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update quotation");
    } finally {
      setUpdatingId(null);
    }
  };

  const filteredQuotations = quotations.filter((q) => statusFilter === "all" || q.status === statusFilter);

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
            <h1 className="text-3xl font-bold mb-2">Quotations</h1>
            <p className="text-muted-foreground">Review and approve customer quotation requests</p>
          </div>
          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-40 bg-card/50 border-border/50">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All</SelectItem>
                <SelectItem value="PENDING">Pending</SelectItem>
                <SelectItem value="APPROVED">Approved</SelectItem>
                <SelectItem value="REJECTED">Rejected</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {(["PENDING", "APPROVED", "REJECTED"] as const).map((status) => {
            const count = quotations.filter((q) => q.status === status).length;
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

        {/* Quotations Table */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left p-4 font-medium text-muted-foreground">Quote ID</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Customer</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Date</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Items</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Total</th>
                    <th className="text-center p-4 font-medium text-muted-foreground">Status</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredQuotations.map((quotation) => {
                    const StatusIcon = statusConfig[quotation.status].icon;
                    return (
                      <tr key={quotation.quotation_id} className="border-b border-border/50 hover:bg-muted/30">
                        <td className="p-4">
                          <span className="font-medium">#{quotation.quotation_id}</span>
                        </td>
                        <td className="p-4 text-muted-foreground">{quotation.user_id}</td>
                        <td className="p-4 text-muted-foreground">{new Date(quotation.created_at).toLocaleDateString()}</td>
                        <td className="p-4 text-right">{quotation.items.length}</td>
                        <td className="p-4 text-right font-medium">LKR {quotation.total_amount.toLocaleString()}</td>
                        <td className="p-4 text-center">
                          <Badge className={cn("border", statusConfig[quotation.status].color)}>
                            <StatusIcon className="h-3 w-3 mr-1" />
                            {statusConfig[quotation.status].label}
                          </Badge>
                        </td>
                        <td className="p-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button variant="ghost" size="sm" onClick={() => setSelectedQuotation(quotation)}>
                              <Eye className="h-4 w-4" />
                            </Button>
                            {quotation.status === "PENDING" && (
                              <>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-green-400 border-green-500/30 hover:bg-green-500/10"
                                  onClick={() => updateQuotationStatus(quotation.quotation_id, "APPROVED")}
                                  disabled={updatingId === quotation.quotation_id}
                                >
                                  Approve
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-red-400 border-red-500/30 hover:bg-red-500/10"
                                  onClick={() => updateQuotationStatus(quotation.quotation_id, "REJECTED")}
                                  disabled={updatingId === quotation.quotation_id}
                                >
                                  Reject
                                </Button>
                              </>
                            )}
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {filteredQuotations.length === 0 && <div className="py-12 text-center text-muted-foreground">No quotations found</div>}
          </CardContent>
        </Card>

        {/* Quotation Detail Dialog */}
        <Dialog open={!!selectedQuotation} onOpenChange={() => setSelectedQuotation(null)}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Quotation #{selectedQuotation?.quotation_id}</DialogTitle>
            </DialogHeader>
            {selectedQuotation && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Status</span>
                  <Badge className={cn("border", statusConfig[selectedQuotation.status].color)}>{statusConfig[selectedQuotation.status].label}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Customer</span>
                  <span>{selectedQuotation.user_id}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Date</span>
                  <span>{new Date(selectedQuotation.created_at).toLocaleString()}</span>
                </div>
                {selectedQuotation.notes && (
                  <div>
                    <span className="text-muted-foreground">Notes</span>
                    <p className="mt-1 text-sm">{selectedQuotation.notes}</p>
                  </div>
                )}
                <Separator />
                <div className="space-y-3">
                  <h4 className="font-medium">Items</h4>
                  {selectedQuotation.items.map((item) => (
                    <div key={item.quotation_item_id} className="flex items-center justify-between py-2">
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
                <Separator />
                <div className="flex items-center justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>LKR {selectedQuotation.total_amount.toLocaleString()}</span>
                </div>
                {selectedQuotation.status === "PENDING" && (
                  <div className="flex gap-3 pt-4">
                    <Button
                      className="flex-1 bg-green-600 hover:bg-green-700"
                      onClick={() => updateQuotationStatus(selectedQuotation.quotation_id, "APPROVED")}
                      disabled={updatingId === selectedQuotation.quotation_id}
                    >
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Approve
                    </Button>
                    <Button
                      variant="destructive"
                      className="flex-1"
                      onClick={() => updateQuotationStatus(selectedQuotation.quotation_id, "REJECTED")}
                      disabled={updatingId === selectedQuotation.quotation_id}
                    >
                      <XCircle className="h-4 w-4 mr-2" />
                      Reject
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
