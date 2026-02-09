"use client";

import { useEffect, useState, useCallback } from "react";
import { AdminLayout } from "@/components/layouts/admin-layout";
import { productActions, supplierActions } from "@/lib/actions";
import { Product, ProductCategory, ProductCreate, Supplier } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu";
import { toast } from "sonner";
import { Plus, Search, MoreVertical, Pencil, Trash2, Package, Truck, ImagePlus, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@clerk/nextjs";

const categories: ProductCategory[] = ["chemicals", "hardware", "tools", "paints", "electrical", "plumbing", "building_materials", "safety_equipment", "other"];

const categoryColors: Record<string, string> = {
  chemicals: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  hardware: "bg-blue-500/10 text-blue-400 border-blue-500/30",
  tools: "bg-orange-500/10 text-orange-400 border-orange-500/30",
  paints: "bg-pink-500/10 text-pink-400 border-pink-500/30",
  electrical: "bg-yellow-500/10 text-yellow-400 border-yellow-500/30",
  plumbing: "bg-cyan-500/10 text-cyan-400 border-cyan-500/30",
  building_materials: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  safety_equipment: "bg-red-500/10 text-red-400 border-red-500/30",
  other: "bg-gray-500/10 text-gray-400 border-gray-500/30",
};

export default function AdminProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState<Product | null>(null);
  const [selectedSupplierId, setSelectedSupplierId] = useState<string>("");
  const [supplyPrice, setSupplyPrice] = useState<number | undefined>(undefined);
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [formData, setFormData] = useState<ProductCreate>({
    name: "",
    price: 0,
    stock_qty: 0,
    category: "other",
    brand: "",
    description: "",
    reorder_level: 10,
  });
  const [authToken, setAuthToken] = useState<string | null>(null);
  const { getToken } = useAuth();
  useEffect(() => {
    const fetchToken = async () => {
      const token = await getToken({ template: "lak-chemicles-and-hardware" });
      setAuthToken(token);
    };
    fetchToken();
  }, [getToken]);

  const fetchProducts = useCallback(async () => {
    try {
      const response = await productActions.getAll(0, 500, true);
      setProducts(response.products);
    } catch {
      toast.error("Failed to fetch products");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchSuppliers = useCallback(async () => {
    try {
      const response = await supplierActions.getAll(0, 500, authToken);
      setSuppliers(response.suppliers.filter((s) => s.is_active));
    } catch {
      // Suppliers fetch failed, continue without suppliers
    }
  }, [authToken]);

  useEffect(() => {
    fetchProducts();
    fetchSuppliers();
  }, [fetchProducts, fetchSuppliers]);

  const resetForm = () => {
    setFormData({
      name: "",
      price: 0,
      stock_qty: 0,
      category: "other",
      brand: "",
      description: "",
      reorder_level: 10,
    });
    setEditingProduct(null);
    setSelectedSupplierId("");
    setSupplyPrice(undefined);
    setImageFile(null);
    setImagePreview(null);
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const clearImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };

  const handleOpenDialog = (product?: Product) => {
    if (product) {
      setEditingProduct(product);
      setFormData({
        name: product.name,
        price: product.price,
        stock_qty: product.stock_qty,
        category: product.category,
        brand: product.brand || "",
        description: product.description || "",
        reorder_level: product.reorder_level,
      });
      // TODO: Could fetch and display current supplier for this product
      setSelectedSupplierId("");
      setSupplyPrice(undefined);
    } else {
      resetForm();
    }
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      let productId: string;

      if (editingProduct) {
        await productActions.update(editingProduct.id, formData, authToken);
        productId = editingProduct.id;
        toast.success("Product updated successfully");
      } else {
        const newProduct = await productActions.create(formData, imageFile || undefined, authToken);
        productId = newProduct.id;
        toast.success("Product created successfully");
      }

      // Link to supplier if one is selected
      if (selectedSupplierId) {
        try {
          await supplierActions.linkProduct(selectedSupplierId, productId, supplyPrice, authToken);
          toast.success("Product linked to supplier");
        } catch {
          toast.error("Product saved but failed to link to supplier");
        }
      }

      setIsDialogOpen(false);
      resetForm();
      fetchProducts();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to save product");
    }
  };

  const handleDelete = async (product: Product) => {
    if (!confirm(`Are you sure you want to delete "${product.name}"?`)) return;

    try {
      await productActions.delete(product.id, false, authToken);
      toast.success("Product deleted successfully");
      fetchProducts();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to delete product");
    }
  };

  const filteredProducts = products.filter((p) => p.name.toLowerCase().includes(searchQuery.toLowerCase()) || p.brand?.toLowerCase().includes(searchQuery.toLowerCase()));

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
            <h1 className="text-3xl font-bold mb-2">Products</h1>
            <p className="text-muted-foreground">Manage your product catalog</p>
          </div>
          <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 bg-orange-500 hover:bg-orange-600" onClick={() => handleOpenDialog()}>
                <Plus className="h-4 w-4" />
                Add Product
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>{editingProduct ? "Edit Product" : "Add New Product"}</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="text-sm font-medium mb-2 block">Name *</label>
                  <Input value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="Product name" required />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Price (LKR) *</label>
                    <Input type="number" value={formData.price} onChange={(e) => setFormData({ ...formData, price: parseFloat(e.target.value) || 0 })} min={0} step={0.01} required />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Stock Qty *</label>
                    <Input type="number" value={formData.stock_qty} onChange={(e) => setFormData({ ...formData, stock_qty: parseInt(e.target.value) || 0 })} min={0} required />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">Category</label>
                    <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value as ProductCategory })}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map((cat) => (
                          <SelectItem key={cat} value={cat}>
                            {cat.replace("_", " ").replace(/\b\w/g, (l) => l.toUpperCase())}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">Brand</label>
                    <Input value={formData.brand} onChange={(e) => setFormData({ ...formData, brand: e.target.value })} placeholder="Brand name" />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">Reorder Level</label>
                  <Input type="number" value={formData.reorder_level} onChange={(e) => setFormData({ ...formData, reorder_level: parseInt(e.target.value) || 0 })} min={0} />
                </div>

                {/* Image Upload Section */}
                {!editingProduct && (
                  <div className="border-t border-border/50 pt-4">
                    <div className="flex items-center gap-2 mb-3">
                      <ImagePlus className="h-4 w-4 text-orange-400" />
                      <span className="text-sm font-medium">Product Image</span>
                    </div>
                    {imagePreview ? (
                      <div className="relative w-32 h-32">
                        <img src={imagePreview} alt="Preview" className="w-full h-full object-cover rounded-lg" />
                        <button type="button" onClick={clearImage} className="absolute -top-2 -right-2 bg-destructive text-destructive-foreground rounded-full p-1 hover:bg-destructive/90">
                          <X className="h-4 w-4" />
                        </button>
                      </div>
                    ) : (
                      <div>
                        <label className="flex flex-col items-center justify-center w-full h-32 border-2 border-dashed border-border/50 rounded-lg cursor-pointer hover:border-orange-500/50 transition-colors">
                          <ImagePlus className="h-8 w-8 text-muted-foreground mb-2" />
                          <span className="text-sm text-muted-foreground">Click to upload image</span>
                          <input type="file" accept="image/*" onChange={handleImageChange} className="hidden" />
                        </label>
                      </div>
                    )}
                  </div>
                )}

                {/* Supplier Assignment Section */}
                <div className="border-t border-border/50 pt-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Truck className="h-4 w-4 text-orange-400" />
                    <span className="text-sm font-medium">Assign Supplier</span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="text-sm font-medium mb-2 block">Supplier</label>
                      <Select value={selectedSupplierId} onValueChange={setSelectedSupplierId}>
                        <SelectTrigger>
                          <SelectValue placeholder="Select supplier" />
                        </SelectTrigger>
                        <SelectContent>
                          {suppliers.map((supplier) => (
                            <SelectItem key={supplier.id} value={supplier.id}>
                              {supplier.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <label className="text-sm font-medium mb-2 block">Supply Price (LKR)</label>
                      <Input
                        type="number"
                        value={supplyPrice ?? ""}
                        onChange={(e) => setSupplyPrice(e.target.value ? parseFloat(e.target.value) : undefined)}
                        placeholder="Cost from supplier"
                        min={0}
                        step={0.01}
                        disabled={!selectedSupplierId}
                      />
                    </div>
                  </div>
                  {suppliers.length === 0 && <p className="text-xs text-muted-foreground mt-2">No suppliers available. Add suppliers first.</p>}
                </div>

                <div>
                  <label className="text-sm font-medium mb-2 block">Description</label>
                  <Textarea value={formData.description} onChange={(e) => setFormData({ ...formData, description: e.target.value })} placeholder="Product description" rows={3} />
                </div>
                <div className="flex gap-3 pt-4">
                  <Button type="button" variant="outline" className="flex-1" onClick={() => setIsDialogOpen(false)}>
                    Cancel
                  </Button>
                  <Button type="submit" className="flex-1 bg-orange-500 hover:bg-orange-600">
                    {editingProduct ? "Update" : "Create"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search products..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10 bg-card/50 border-border/50" />
        </div>

        {/* Products Table */}
        <Card className="bg-card/50 border-border/50">
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border/50">
                    <th className="text-left p-4 font-medium text-muted-foreground">Product</th>
                    <th className="text-left p-4 font-medium text-muted-foreground">Category</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Price</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Stock</th>
                    <th className="text-center p-4 font-medium text-muted-foreground">Status</th>
                    <th className="text-right p-4 font-medium text-muted-foreground">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredProducts.map((product) => {
                    const isLowStock = product.stock_qty <= product.reorder_level;
                    const isOutOfStock = product.stock_qty === 0;

                    return (
                      <tr key={product.id} className="border-b border-border/50 hover:bg-muted/30">
                        <td className="p-4">
                          <div className="flex items-center gap-3">
                            <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
                              <Package className="h-5 w-5 text-muted-foreground/50" />
                            </div>
                            <div>
                              <p className="font-medium">{product.name}</p>
                              {product.brand && <p className="text-sm text-muted-foreground">{product.brand}</p>}
                            </div>
                          </div>
                        </td>
                        <td className="p-4">
                          <Badge className={cn("border", categoryColors[product.category])}>{product.category.replace("_", " ")}</Badge>
                        </td>
                        <td className="p-4 text-right font-medium">LKR {product.price.toLocaleString()}</td>
                        <td className="p-4 text-right">{product.stock_qty}</td>
                        <td className="p-4 text-center">
                          {isOutOfStock ? (
                            <Badge variant="destructive">Out of Stock</Badge>
                          ) : isLowStock ? (
                            <Badge className="bg-yellow-500/10 text-yellow-400 border-yellow-500/30">Low Stock</Badge>
                          ) : (
                            <Badge className="bg-green-500/10 text-green-400 border-green-500/30">In Stock</Badge>
                          )}
                        </td>
                        <td className="p-4 text-right">
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon">
                                <MoreVertical className="h-4 w-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem onClick={() => handleOpenDialog(product)}>
                                <Pencil className="h-4 w-4 mr-2" />
                                Edit
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={() => handleDelete(product)} className="text-destructive">
                                <Trash2 className="h-4 w-4 mr-2" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            {filteredProducts.length === 0 && <div className="py-12 text-center text-muted-foreground">No products found</div>}
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
}
