"use client";

import { Product } from "@/lib/types";
import { Card, CardContent, CardFooter } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ShoppingCart, Eye, Package } from "lucide-react";
import { cn } from "@/lib/utils";
import { cartActions } from "@/lib/actions";
import { toast } from "sonner";
import { useState } from "react";
import Link from "next/link";
import Image from "next/image";

interface ProductCardProps {
  product: Product;
  onAddToCart?: () => void;
}

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

export function ProductCard({ product, onAddToCart }: ProductCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleAddToCart = async () => {
    setIsLoading(true);
    try {
      await cartActions.addItem({
        product_id: product.id,
        quantity: 1,
      });
      toast.success(`${product.name} added to cart!`);
      onAddToCart?.();
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to add to cart");
    } finally {
      setIsLoading(false);
    }
  };

  const isLowStock = product.stock_qty <= product.reorder_level;
  const isOutOfStock = product.stock_qty === 0;

  return (
    <Card className="group relative overflow-hidden bg-card/50 border-border/50 hover:border-orange-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/5">
      {/* Product Image */}
      <div className="relative aspect-square overflow-hidden bg-linear-to-br from-muted/50 to-muted">
        {product.image_url ? (
          <Image src={product.image_url} alt={product.name} width={500} height={500} className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110" />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <Package className="h-16 w-16 text-muted-foreground/30" />
          </div>
        )}

        {/* Quick View Overlay */}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
          <Link href={`/products/${product.id}`}>
            <Button variant="secondary" size="sm" className="gap-2">
              <Eye className="h-4 w-4" />
              Quick View
            </Button>
          </Link>
        </div>

        {/* Category Badge */}
        <Badge className={cn("absolute top-3 left-3 text-xs font-medium border", categoryColors[product.category] || categoryColors.other)}>{product.category.replace("_", " ")}</Badge>

        {/* Stock Status */}
        {isOutOfStock && (
          <Badge variant="destructive" className="absolute top-3 right-3">
            Out of Stock
          </Badge>
        )}
        {isLowStock && !isOutOfStock && <Badge className="absolute top-3 right-3 bg-yellow-500/10 text-yellow-400 border-yellow-500/30">Low Stock</Badge>}
      </div>

      <CardContent className="p-4">
        {/* Brand */}
        {product.brand && <p className="text-xs text-muted-foreground mb-1">{product.brand}</p>}

        {/* Name */}
        <h3 className="font-semibold text-foreground line-clamp-2 mb-2 group-hover:text-orange-400 transition-colors">{product.name}</h3>

        {/* Price */}
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-foreground">LKR {product.price.toLocaleString()}</span>
        </div>

        {/* Stock Info */}
        <p className="text-xs text-muted-foreground mt-2">{product.stock_qty} in stock</p>
      </CardContent>

      <CardFooter className="p-4 pt-0">
        <Button className="w-full gap-2 bg-orange-500 hover:bg-orange-600 text-white" disabled={isOutOfStock || isLoading} onClick={handleAddToCart}>
          <ShoppingCart className="h-4 w-4" />
          {isLoading ? "Adding..." : isOutOfStock ? "Out of Stock" : "Add to Cart"}
        </Button>
      </CardFooter>
    </Card>
  );
}
