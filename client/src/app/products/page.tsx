"use client";

import { useEffect, useState, useCallback } from "react";
import { CustomerLayout } from "@/components/layouts/customer-layout";
import { ProductGrid } from "@/components/products/product-grid";
import { productActions } from "@/lib/actions";
import { Product } from "@/lib/types";
import { Spinner } from "@/components/ui/spinner";
import { Button } from "@/components/ui/button";
import { RefreshCw } from "lucide-react";

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProducts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await productActions.getAll(0, 500);
      setProducts(response.products);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch products");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  return (
    <CustomerLayout>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">All Products</h1>
          <p className="text-muted-foreground">Browse our complete catalog of chemicals, hardware, and tools</p>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex items-center justify-center py-20">
            <Spinner className="h-8 w-8" />
          </div>
        )}

        {/* Error State */}
        {error && !isLoading && (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <p className="text-destructive mb-4">{error}</p>
            <Button onClick={fetchProducts} variant="outline" className="gap-2">
              <RefreshCw className="h-4 w-4" />
              Try Again
            </Button>
          </div>
        )}

        {/* Products Grid */}
        {!isLoading && !error && <ProductGrid products={products} onRefresh={fetchProducts} />}
      </div>
    </CustomerLayout>
  );
}
