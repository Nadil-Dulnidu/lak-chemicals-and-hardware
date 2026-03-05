"use client";

import { useEffect, useState, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { supplierActions, productActions } from "@/lib/actions";
import { Supplier, SupplierCreate, SupplierDetail, Product } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "@/components/ui/dialog";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";
import { Plus, Search, MoreVertical, Pencil, Trash2, Truck, Phone, Mail, MapPin, User, Package, Eye, Link2, Unlink, ArrowLeft, DollarSign, CalendarDays, Box } from "lucide-react";

export default function AdminSuppliersPage() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingSupplier, setEditingSupplier] = useState<Supplier | null>(null);
  const [formData, setFormData] = useState<SupplierCreate>({
    name: "",
    contact_person: "",
    email: "",
    contact_number: "",
    address: "",
  });

  // Detail view state
  const [selectedSupplier, setSelectedSupplier] = useState<SupplierDetail | null>(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);

  // Link product state
  const [showLinkDialog, setShowLinkDialog] = useState(false);
  const [allProducts, setAllProducts] = useState<Product[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<string>("");
  const [supplyPrice, setSupplyPrice] = useState<string>("");
  const [isLinking, setIsLinking] = useState(false);

  const [authToken, setAuthToken] = useState<string | null>(null);
  const { getToken } = useAuth();
  useEffect(() => {
    const fetchToken = async () => {
      const token = await getToken({ template: "lak-chemicles-and-hardware" });
      setAuthToken(token);
    };
    fetchToken();
  }, [getToken]);

  const fetchSuppliers = useCallback(async () => {
    if (!authToken) return;
    try {
      const response = await supplierActions.getAll(0, 500, authToken);
      setSuppliers(response.suppliers);
    } catch {
      toast.error("Failed to fetch suppliers");
    } finally {
      setIsLoading(false);
    }
  }, [authToken]);

  useEffect(() => {
    if (authToken !== null) {
      fetchSuppliers();
    }
  }, [fetchSuppliers, authToken]);

  const resetForm = () => {
    setFormData({
      name: "",
      contact_person: "",
      email: "",
      contact_number: "",
      address: "",
    });
    setEditingSupplier(null);
  };

  const handleOpenDialog = (supplier?: Supplier) => {
    if (supplier) {
      setEditingSupplier(supplier);
      setFormData({
        name: supplier.name,
        contact_person: supplier.contact_person || "",
        email: supplier.email,
        contact_number: supplier.contact_number,
        address: supplier.address || "",
      });
    } else {
      resetForm();
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      if (editingSupplier) {
        await supplierActions.update(editingSupplier.id, formData, authToken);
        toast.success("Supplier updated successfully");
      } else {
        await supplierActions.create(formData, authToken);
        toast.success("Supplier created successfully");
      }
      setIsDialogOpen(false);
      resetForm();
      fetchSuppliers();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to save supplier");
    }
  };

  const handleDelete = async (supplier: Supplier) => {
    if (!confirm(`Are you sure you want to delete "${supplier.name}"?`)) return;

    try {
      await supplierActions.delete(supplier.id, authToken);
      toast.success("Supplier deleted successfully");
      fetchSuppliers();
      if (selectedSupplier?.id === supplier.id) setSelectedSupplier(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to delete supplier";
      toast.error(message, { duration: 5000 });
    }
  };

  // ── Detail View ─────────────────────────────────────────────────────────
  const viewSupplierDetail = async (supplier: Supplier) => {
    setIsDetailLoading(true);
    try {
      const detail = await supplierActions.getDetail(supplier.id, authToken);
      setSelectedSupplier(detail);
    } catch {
      toast.error("Failed to load supplier details");
    } finally {
      setIsDetailLoading(false);
    }
  };

  // ── Link / Unlink Products ──────────────────────────────────────────────
  const openLinkDialog = async () => {
    try {
      const response = await productActions.getAll(0, 500, true);
      // Filter out products already linked
      const linkedIds = new Set(selectedSupplier?.products.map((p) => p.product_id) || []);
      setAllProducts(response.products.filter((p: Product) => !linkedIds.has(p.id)));
      setSelectedProductId("");
      setSupplyPrice("");
      setShowLinkDialog(true);
    } catch {
      toast.error("Failed to load products");
    }
  };

  const handleLinkProduct = async () => {
    if (!selectedSupplier || !selectedProductId) return;
    setIsLinking(true);
    try {
      const price = parseFloat(supplyPrice) || undefined;
      await supplierActions.linkProduct(selectedSupplier.id, selectedProductId, price, authToken);
      toast.success("Product linked successfully");
      setShowLinkDialog(false);
      // Refresh detail
      const detail = await supplierActions.getDetail(selectedSupplier.id, authToken);
      setSelectedSupplier(detail);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to link product");
    } finally {
      setIsLinking(false);
    }
  };

  const handleUnlinkProduct = async (productId: string, productName: string) => {
    if (!selectedSupplier || !confirm(`Unlink "${productName}" from this supplier?`)) return;
    try {
      await supplierActions.unlinkProduct(selectedSupplier.id, productId, authToken);
      toast.success("Product unlinked");
      // Refresh detail
      const detail = await supplierActions.getDetail(selectedSupplier.id, authToken);
      setSelectedSupplier(detail);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to unlink product");
    }
  };

  const filteredSuppliers = suppliers.filter((s) => s.name.toLowerCase().includes(searchQuery.toLowerCase()) || s.contact_person?.toLowerCase().includes(searchQuery.toLowerCase()));

  if (isLoading) {
    return (
      <AdminLayout>
        <div className="flex justify-center items-center min-h-[60vh]">
          <Spinner className="h-8 w-8" />
        </div>
      </AdminLayout>
    );
  }

  // ═══════════════════════════════════════════════════════════════════════
  //  SUPPLIER DETAIL VIEW
  // ═══════════════════════════════════════════════════════════════════════
  if (selectedSupplier) {
    return (
      <AdminLayout>
        <div className="space-y-6">
          {/* Back button + header */}
          <div className="flex items-center gap-4">
            <Button variant="ghost" size="icon" onClick={() => setSelectedSupplier(null)}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex-1">
              <div className="flex items-center gap-3">
                <div className="p-3 rounded-xl bg-orange-500/10">
                  <Truck className="h-6 w-6 text-orange-400" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">{selectedSupplier.name}</h1>
                  <Badge variant="outline" className={selectedSupplier.is_active ? "bg-green-500/10 text-green-400 border-green-500/30" : "bg-red-500/10 text-red-400 border-red-500/30"}>
                    {selectedSupplier.is_active ? "Active" : "Inactive"}
                  </Badge>
                </div>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={() => handleOpenDialog(selectedSupplier)}>
              <Pencil className="h-4 w-4 mr-2" />
              Edit
            </Button>
          </div>

          {/* Supplier Info Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {selectedSupplier.contact_person && (
              <Card className="bg-card/50 border-border/50">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <User className="h-4 w-4 text-blue-400" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Contact Person</p>
                    <p className="font-medium text-sm">{selectedSupplier.contact_person}</p>
                  </div>
                </CardContent>
              </Card>
            )}
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-green-500/10">
                  <Phone className="h-4 w-4 text-green-400" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Phone</p>
                  <p className="font-medium text-sm">{selectedSupplier.contact_number}</p>
                </div>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-4 flex items-center gap-3">
                <div className="p-2 rounded-lg bg-purple-500/10">
                  <Mail className="h-4 w-4 text-purple-400" />
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Email</p>
                  <p className="font-medium text-sm truncate max-w-[180px]">{selectedSupplier.email}</p>
                </div>
              </CardContent>
            </Card>
            {selectedSupplier.address && (
              <Card className="bg-card/50 border-border/50">
                <CardContent className="p-4 flex items-center gap-3">
                  <div className="p-2 rounded-lg bg-amber-500/10">
                    <MapPin className="h-4 w-4 text-amber-400" />
                  </div>
                  <div>
                    <p className="text-xs text-muted-foreground">Address</p>
                    <p className="font-medium text-sm line-clamp-1">{selectedSupplier.address}</p>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Summary Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Linked Products</p>
                  <p className="text-2xl font-bold">{selectedSupplier.products.length}</p>
                </div>
                <div className="p-3 rounded-xl bg-orange-500/10">
                  <Package className="h-5 w-5 text-orange-400" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Since</p>
                  <p className="text-2xl font-bold">{new Date(selectedSupplier.created_at).toLocaleDateString("en-US", { month: "short", year: "numeric" })}</p>
                </div>
                <div className="p-3 rounded-xl bg-blue-500/10">
                  <CalendarDays className="h-5 w-5 text-blue-400" />
                </div>
              </CardContent>
            </Card>
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-4 flex items-center justify-between">
                <div>
                  <p className="text-sm text-muted-foreground">Last Purchase</p>
                  <p className="text-2xl font-bold">
                    {selectedSupplier.last_purchase_date
                      ? new Date(selectedSupplier.last_purchase_date).toLocaleDateString("en-US", {
                          month: "short",
                          day: "numeric",
                        })
                      : "—"}
                  </p>
                </div>
                <div className="p-3 rounded-xl bg-green-500/10">
                  <DollarSign className="h-5 w-5 text-green-400" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Products Section */}
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-6 pb-4">
                <div>
                  <h2 className="text-lg font-semibold">Supplied Products</h2>
                  <p className="text-sm text-muted-foreground">Products provided by this supplier</p>
                </div>
                <Button className="gap-2 bg-orange-500 hover:bg-orange-600" onClick={openLinkDialog}>
                  <Link2 className="h-4 w-4" />
                  Link Product
                </Button>
              </div>
              <Separator />

              {selectedSupplier.products.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <Box className="h-12 w-12 text-muted-foreground/30 mb-3" />
                  <h3 className="font-medium mb-1">No products linked</h3>
                  <p className="text-sm text-muted-foreground mb-4">Link products to track what this supplier provides</p>
                  <Button variant="outline" size="sm" onClick={openLinkDialog}>
                    <Link2 className="h-4 w-4 mr-2" />
                    Link First Product
                  </Button>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-border/50">
                        <th className="text-left p-4 font-medium text-muted-foreground">Product</th>
                        <th className="text-right p-4 font-medium text-muted-foreground">Supply Price</th>
                        <th className="text-right p-4 font-medium text-muted-foreground">Last Supplied</th>
                        <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {selectedSupplier.products.map((product) => (
                        <tr key={product.product_id} className="border-b border-border/50 hover:bg-muted/30">
                          <td className="p-4">
                            <div className="flex items-center gap-3">
                              <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                                <Package className="h-5 w-5 text-muted-foreground/50" />
                              </div>
                              <div>
                                <p className="font-medium">{product.product_name}</p>
                                <p className="text-xs text-muted-foreground font-mono">{product.product_id.slice(0, 8)}...</p>
                              </div>
                            </div>
                          </td>
                          <td className="p-4 text-right">
                            {product.supply_price ? (
                              <span className="font-medium text-green-400">
                                LKR{" "}
                                {product.supply_price.toLocaleString(undefined, {
                                  minimumFractionDigits: 2,
                                })}
                              </span>
                            ) : (
                              <span className="text-muted-foreground">—</span>
                            )}
                          </td>
                          <td className="p-4 text-right text-muted-foreground">{product.last_supplied_date ? new Date(product.last_supplied_date).toLocaleDateString() : "—"}</td>
                          <td className="p-4 text-right">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                              onClick={() => handleUnlinkProduct(product.product_id, product.product_name)}
                            >
                              <Unlink className="h-4 w-4 mr-1" />
                              Unlink
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

          {/* Link Product Dialog */}
          <Dialog open={showLinkDialog} onOpenChange={setShowLinkDialog}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Link Product to {selectedSupplier.name}</DialogTitle>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Select Product *</label>
                  <Select value={selectedProductId} onValueChange={setSelectedProductId}>
                    <SelectTrigger className="bg-card/50 border-border/50">
                      <SelectValue placeholder="Choose a product..." />
                    </SelectTrigger>
                    <SelectContent>
                      {allProducts.map((product) => (
                        <SelectItem key={product.id} value={product.id}>
                          {product.name} — LKR {product.price.toLocaleString()}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {allProducts.length === 0 && <p className="text-xs text-muted-foreground mt-2">All products are already linked to this supplier.</p>}
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Supply Price (LKR)</label>
                  <div className="relative">
                    <DollarSign className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input type="number" placeholder="0.00" className="pl-9" value={supplyPrice} onChange={(e) => setSupplyPrice(e.target.value)} />
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">Optional — price at which this supplier provides the product</p>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setShowLinkDialog(false)}>
                  Cancel
                </Button>
                <Button className="bg-orange-500 hover:bg-orange-600" onClick={handleLinkProduct} disabled={!selectedProductId || isLinking}>
                  {isLinking ? <Spinner className="h-4 w-4 mr-2" /> : <Link2 className="h-4 w-4 mr-2" />}
                  Link Product
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>

        {/* Edit Dialog — shared with list view */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>{editingSupplier ? "Edit Supplier" : "Add New Supplier"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">Company Name *</label>
                <Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="Supplier name" required />
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Contact Person</label>
                <Input value={formData.contact_person} onChange={(e) => setFormData({ ...formData, contact_person: e.target.value })} placeholder="Contact person name" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Email *</label>
                  <Input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} placeholder="email@example.com" required />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Phone *</label>
                  <Input
                    value={formData.contact_number}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        contact_number: e.target.value,
                      })
                    }
                    placeholder="+94 XX XXX XXXX"
                    required
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Address</label>
                <Textarea value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} placeholder="Full address" rows={3} />
              </div>
              <div className="flex gap-3 pt-4">
                <Button type="button" variant="outline" className="flex-1" onClick={() => setIsDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" className="flex-1 bg-orange-500 hover:bg-orange-600">
                  {editingSupplier ? "Update" : "Create"}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </AdminLayout>
    );
  }

  // ═══════════════════════════════════════════════════════════════════════
  //  SUPPLIER LIST VIEW
  // ═══════════════════════════════════════════════════════════════════════
  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold mb-2">Suppliers</h1>
            <p className="text-muted-foreground">Manage your supplier relationships and product links</p>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 bg-orange-500 hover:bg-orange-600" onClick={() => handleOpenDialog()}>
                <Plus className="h-4 w-4" />
                Add Supplier
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg">
              <DialogHeader>
                <DialogTitle>{editingSupplier ? "Edit Supplier" : "Add New Supplier"}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Company Name *</label>
                  <Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="Supplier name" required />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Contact Person</label>
                  <Input
                    value={formData.contact_person}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        contact_person: e.target.value,
                      })
                    }
                    placeholder="Contact person name"
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Email *</label>
                    <Input type="email" value={formData.email} onChange={(e) => setFormData({ ...formData, email: e.target.value })} placeholder="email@example.com" required />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Phone *</label>
                    <Input
                      value={formData.contact_number}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          contact_number: e.target.value,
                        })
                      }
                      placeholder="+94 XX XXX XXXX"
                      required
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Address</label>
                  <Textarea value={formData.address} onChange={(e) => setFormData({ ...formData, address: e.target.value })} placeholder="Full address" rows={3} />
                </div>
                <div className="flex gap-3 pt-4">
                  <Button type="button" variant="outline" className="flex-1" onClick={() => setIsDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" className="flex-1 bg-orange-500 hover:bg-orange-600">
                    {editingSupplier ? "Update" : "Create"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Suppliers</p>
                <p className="text-2xl font-bold">{suppliers.length}</p>
              </div>
              <div className="p-3 rounded-xl bg-orange-500/10">
                <Truck className="h-5 w-5 text-orange-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Active</p>
                <p className="text-2xl font-bold">{suppliers.filter((s) => s.is_active).length}</p>
              </div>
              <div className="p-3 rounded-xl bg-green-500/10">
                <Truck className="h-5 w-5 text-green-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-card/50 border-border/50">
            <CardContent className="p-4 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Inactive</p>
                <p className="text-2xl font-bold">{suppliers.filter((s) => !s.is_active).length}</p>
              </div>
              <div className="p-3 rounded-xl bg-red-500/10">
                <Truck className="h-5 w-5 text-red-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search suppliers..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10 bg-card/50 border-border/50" />
        </div>

        {/* Suppliers Table */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left p-4 font-medium text-muted-foreground">Supplier</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Contact</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Email</th>
                    <th className="text-center p-4 font-medium text-muted-foreground">Status</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredSuppliers.map((supplier) => (
                    <tr key={supplier.id} className="border-b border-border/50 hover:bg-muted/30 cursor-pointer" onClick={() => viewSupplierDetail(supplier)}>
                      <td className="p-4">
                        <div className="flex items-center gap-3">
                          <div className="p-2 rounded-lg bg-orange-500/10">
                            <Truck className="h-4 w-4 text-orange-400" />
                          </div>
                          <div>
                            <p className="font-medium">{supplier.name}</p>
                            {supplier.contact_person && <p className="text-xs text-muted-foreground">{supplier.contact_person}</p>}
                          </div>
                        </div>
                      </td>
                      <td className="p-4 text-muted-foreground text-sm">{supplier.contact_number}</td>
                      <td className="p-4 text-muted-foreground text-sm">{supplier.email}</td>
                      <td className="p-4 text-center">
                        <Badge variant="outline" className={supplier.is_active ? "bg-green-500/10 text-green-400 border-green-500/30" : "bg-red-500/10 text-red-400 border-red-500/30"}>
                          {supplier.is_active ? "Active" : "Inactive"}
                        </Badge>
                      </td>
                      <td className="p-4 text-right">
                        <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="sm" onClick={() => viewSupplierDetail(supplier)} disabled={isDetailLoading}>
                            <Eye className="h-4 w-4" />
                          </Button>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleOpenDialog(supplier)}>
                                <Pencil className="h-4 w-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleDelete(supplier)} className="text-destructive">
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {filteredSuppliers.length === 0 && (
              <div className="flex flex-col items-center justify-center py-20 text-center">
                <Truck className="h-16 w-16 text-muted-foreground/30 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No suppliers found</h3>
                <p className="text-muted-foreground">Add your first supplier to get started</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
}
