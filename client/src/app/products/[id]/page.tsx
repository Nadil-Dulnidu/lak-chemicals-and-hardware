"use client";

import { useEffect, useState, use } from "react";
import { CustomerLayout } from "@/components/layouts/customer-layout";
import { productActions, cartActions } from "@/lib/actions";
import { Product } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import { Input } from "@/components/ui/input";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import Link from "next/link";
import { ShoppingCart, Package, ArrowLeft, Minus, Plus, Truck, Shield, RotateCcw, CheckCircle, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@clerk/nextjs";

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

interface ProductDetailPageProps {
  params: Promise<{ id: string }>;
}

export default function ProductDetailPage({ params }: ProductDetailPageProps) {
  const { id } = use(params);
  const [product, setProduct] = useState<Product | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [isAddingToCart, setIsAddingToCart] = useState(false);

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
    const fetchProduct = async () => {
      try {
        const data = await productActions.getById(id);
        setProduct(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Product not found");
      } finally {
        setIsLoading(false);
      }
    };

    fetchProduct();
  }, [id]);

  const handleAddToCart = async () => {
    if (!product) return;

    setIsAddingToCart(true);
    try {
      await cartActions.addItem(
        {
          product_id: product.id,
          quantity,
        },
        authToken,
      );
      toast.success(`${quantity} × ${product.name} added to cart!`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to add to cart");
    } finally {
      setIsAddingToCart(false);
    }
  };

  const incrementQuantity = () => {
    if (product && quantity < product.stock_qty) {
      setQuantity((q) => q + 1);
    }
  };

  const decrementQuantity = () => {
    if (quantity > 1) {
      setQuantity((q) => q - 1);
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

  if (error || !product) {
    return (
      <CustomerLayout>
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
            <Package className="h-20 w-20 text-muted-foreground/30 mb-6" />
            <h1 className="text-2xl font-bold mb-2">Product Not Found</h1>
            <p className="text-muted-foreground mb-6">{error || "The product you're looking for doesn't exist"}</p>
            <Link href="/products">
              <Button variant="outline" className="gap-2">
                <ArrowLeft className="h-4 w-4" />
                Back to Products
              </Button>
            </Link>
          </div>
        </div>
      </CustomerLayout>
    );
  }

  const isLowStock = product.stock_qty <= product.reorder_level;
  const isOutOfStock = product.stock_qty === 0;

  return (
    <CustomerLayout>
      <div className="container mx-auto px-4 py-8">
        {/* Breadcrumb */}
        <div className="mb-6">
          <Link href="/products" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors">
            <ArrowLeft className="h-4 w-4" />
            Back to Products
          </Link>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12">
          {/* Product Image */}
          <div className="relative">
            <div className="aspect-square rounded-2xl overflow-hidden bg-gradient-to-br from-muted/50 to-muted border border-border/50">
              {product.image_url ? (
                <img src={product.image_url} alt={product.name} className="w-full h-full object-cover" />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <Package className="h-32 w-32 text-muted-foreground/20" />
                </div>
              )}
            </div>

            {/* Status Badges */}
            <div className="absolute top-4 left-4 flex flex-col gap-2">
              <Badge className={cn("text-sm font-medium border", categoryColors[product.category] || categoryColors.other)}>{product.category.replace("_", " ")}</Badge>
              {isOutOfStock && (
                <Badge variant="destructive" className="text-sm">
                  Out of Stock
                </Badge>
              )}
              {isLowStock && !isOutOfStock && <Badge className="text-sm bg-yellow-500/10 text-yellow-400 border-yellow-500/30">Only {product.stock_qty} left</Badge>}
            </div>
          </div>

          {/* Product Details */}
          <div className="space-y-6">
            {/* Brand & Name */}
            {product.brand && <p className="text-sm text-orange-400 font-medium">{product.brand}</p>}
            <h1 className="text-3xl md:text-4xl font-bold">{product.name}</h1>

            {/* Price */}
            <div className="flex items-baseline gap-3">
              <span className="text-4xl font-bold text-foreground">LKR {product.price.toLocaleString()}</span>
            </div>

            {/* Stock Status */}
            <div className="flex items-center gap-2">
              {isOutOfStock ? (
                <>
                  <AlertTriangle className="h-5 w-5 text-destructive" />
                  <span className="text-destructive font-medium">Out of Stock</span>
                </>
              ) : isLowStock ? (
                <>
                  <AlertTriangle className="h-5 w-5 text-yellow-400" />
                  <span className="text-yellow-400 font-medium">Low Stock - {product.stock_qty} available</span>
                </>
              ) : (
                <>
                  <CheckCircle className="h-5 w-5 text-green-400" />
                  <span className="text-green-400 font-medium">In Stock - {product.stock_qty} available</span>
                </>
              )}
            </div>

            <Separator />

            {/* Description */}
            {product.description && (
              <div>
                <h3 className="font-semibold mb-2">Description</h3>
                <p className="text-muted-foreground leading-relaxed">{product.description}</p>
              </div>
            )}

            {/* Quantity Selector */}
            <div className="space-y-3">
              <label className="font-semibold">Quantity</label>
              <div className="flex items-center gap-3">
                <Button variant="outline" size="icon" onClick={decrementQuantity} disabled={quantity <= 1 || isOutOfStock}>
                  <Minus className="h-4 w-4" />
                </Button>
                <Input
                  type="number"
                  value={quantity}
                  onChange={(e) => {
                    const val = parseInt(e.target.value) || 1;
                    setQuantity(Math.min(Math.max(1, val), product.stock_qty));
                  }}
                  className="w-20 text-center"
                  min={1}
                  max={product.stock_qty}
                  disabled={isOutOfStock}
                />
                <Button variant="outline" size="icon" onClick={incrementQuantity} disabled={quantity >= product.stock_qty || isOutOfStock}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Add to Cart */}
            <Button size="lg" className="w-full gap-3 h-14 text-lg bg-orange-500 hover:bg-orange-600" onClick={handleAddToCart} disabled={isOutOfStock || isAddingToCart}>
              <ShoppingCart className="h-5 w-5" />
              {isAddingToCart ? "Adding..." : isOutOfStock ? "Out of Stock" : `Add to Cart - LKR ${(product.price * quantity).toLocaleString()}`}
            </Button>

            <Separator />

            {/* Features */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-card/50 border border-border/50">
                <Truck className="h-5 w-5 text-orange-400" />
                <div>
                  <p className="text-sm font-medium">Fast Delivery</p>
                  <p className="text-xs text-muted-foreground">2-3 business days</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-card/50 border border-border/50">
                <Shield className="h-5 w-5 text-orange-400" />
                <div>
                  <p className="text-sm font-medium">Quality Assured</p>
                  <p className="text-xs text-muted-foreground">100% Genuine</p>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-card/50 border border-border/50">
                <RotateCcw className="h-5 w-5 text-orange-400" />
                <div>
                  <p className="text-sm font-medium">Easy Returns</p>
                  <p className="text-xs text-muted-foreground">7-day return policy</p>
                </div>
              </div>
            </div>

            {/* Product Info */}
            <Card className="bg-card/50 border-border/50">
              <CardContent className="p-4 space-y-3">
                <h3 className="font-semibold">Product Details</h3>
                <div className="grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <span className="text-muted-foreground">Product ID</span>
                    <p className="font-medium">{product.id}</p>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Category</span>
                    <p className="font-medium capitalize">{product.category.replace("_", " ")}</p>
                  </div>
                  {product.brand && (
                    <div>
                      <span className="text-muted-foreground">Brand</span>
                      <p className="font-medium">{product.brand}</p>
                    </div>
                  )}
                  <div>
                    <span className="text-muted-foreground">Stock</span>
                    <p className="font-medium">{product.stock_qty} units</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </CustomerLayout>
  );
}
