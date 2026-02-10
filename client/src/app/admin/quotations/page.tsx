// Update file: c:\nadil-dulnidu\lak-chemicals-and-hardware\client\src\app\admin\quotations\page.tsx
"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { quotationActions } from "@/lib/actions";
import { Quotation } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { toast } from "sonner";
import { Clock, CheckCircle, XCircle, Eye, Package, Filter, DollarSign } from "lucide-react";
import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

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

  // Discount state
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [discountAmount, setDiscountAmount] = useState<string>("0");

  const [authToken, setAuthToken] = useState<string | null>(null);
  const { getToken } = useAuth();
  useEffect(() => {
    const fetchToken = async () => {
      const token = await getToken({ template: "lak-chemicles-and-hardware" });
      setAuthToken(token);
    };
    fetchToken();
  }, [getToken]);

  const fetchQuotations = useCallback(async () => {
    if (!authToken) return;
    try {
      const response = await quotationActions.getAll(0, 500, authToken);
      setQuotations(response.quotations);
    } catch (error) {
      // Suppressing the unused variable error
      console.error(error);
      toast.error("Failed to fetch quotations");
    } finally {
      setIsLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    if (authToken !== null) {
      fetchQuotations();
    }
  }, [fetchQuotations, authToken]);

  const handleApproveClick = (quotation: Quotation) => {
    setSelectedQuotation(quotation);
    setShowApproveDialog(true);
    setDiscountAmount("0");
  };

  const confirmApprove = async () => {
    if (!selectedQuotation) return;

    setUpdatingId(selectedQuotation.quotation_id);
    try {
      const discount = parseFloat(discountAmount) || 0;
      await quotationActions.updateStatus(selectedQuotation.quotation_id, "APPROVED", discount, authToken);
      toast.success("Quotation approved successfully");
      fetchQuotations();
      setShowApproveDialog(false);
      setSelectedQuotation(null);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to approve quotation");
    } finally {
      setUpdatingId(null);
    }
  };

  const handleReject = async (quotationId: number) => {
    setUpdatingId(quotationId);
    try {
      await quotationActions.updateStatus(quotationId, "REJECTED", undefined, authToken);
      toast.success("Quotation rejected");
      fetchQuotations();
      if (selectedQuotation?.quotation_id === quotationId) {
        setSelectedQuotation(null);
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to reject quotation");
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
                                  onClick={() => handleApproveClick(quotation)}
                                  disabled={updatingId === quotation.quotation_id}
                                >
                                  Approve
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  className="text-red-400 border-red-500/30 hover:bg-red-500/10"
                                  onClick={() => handleReject(quotation.quotation_id)}
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
        <Dialog open={!!selectedQuotation && !showApproveDialog} onOpenChange={() => setSelectedQuotation(null)}>
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

                {selectedQuotation.discount_amount && selectedQuotation.discount_amount > 0 && (
                  <div className="flex items-center justify-between text-green-500">
                    <span>Discount Applied</span>
                    <span>- LKR {selectedQuotation.discount_amount.toLocaleString()}</span>
                  </div>
                )}

                <div className="flex items-center justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>LKR {(selectedQuotation.total_amount - (selectedQuotation.discount_amount || 0)).toLocaleString()}</span>
                </div>

                {selectedQuotation.status === "PENDING" && (
                  <div className="flex gap-3 pt-4">
                    <Button className="flex-1 bg-green-600 hover:bg-green-700" onClick={() => handleApproveClick(selectedQuotation)} disabled={updatingId === selectedQuotation.quotation_id}>
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Approve
                    </Button>
                    <Button variant="destructive" className="flex-1" onClick={() => handleReject(selectedQuotation.quotation_id)} disabled={updatingId === selectedQuotation.quotation_id}>
                      <XCircle className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                )}
              </div>
            )}
          </DialogContent>
        </Dialog>

        {/* Approve Dialog */}
        <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Approve Quotation #{selectedQuotation?.quotation_id}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <p className="font-medium mb-1">Current Total: LKR {selectedQuotation?.total_amount.toLocaleString()}</p>
                <p className="text-sm text-muted-foreground mb-4">You can optionally offer a discount to close the deal.</p>
              </div>
              <div className="grid gap-2">
                <Label htmlFor="discount">Discount Amount (LKR)</Label>
                <div className="relative">
                  <DollarSign className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                  <Input id="discount" type="number" placeholder="0.00" className="pl-9" value={discountAmount} onChange={(e) => setDiscountAmount(e.target.value)} />
                </div>
              </div>
              <div className="bg-muted/30 p-3 rounded-lg flex justify-between items-center">
                <span className="font-medium">New Total:</span>
                <span className="font-bold text-lg text-primary">
                  LKR{" "}
                  {(selectedQuotation?.total_amount || 0) - (parseFloat(discountAmount) || 0) < 0 ? 0 : ((selectedQuotation?.total_amount || 0) - (parseFloat(discountAmount) || 0)).toLocaleString()}
                </span>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowApproveDialog(false)}>
                Cancel
              </Button>
              <Button onClick={confirmApprove} className="bg-green-600 hover:bg-green-700">
                Confirm Approval
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </AdminLayout>
  );
}
