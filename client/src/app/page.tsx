"use client";

import { useEffect, useState } from "react";
import { CustomerLayout } from "@/components/layouts/customer-layout";
import { ProductCard } from "@/components/products/product-card";
import { productActions } from "@/lib/actions";
import { Product } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Spinner } from "@/components/ui/spinner";
import Link from "next/link";
import { Paintbrush, Zap, Droplets, FlaskConical, Shield, ArrowRight, Truck, Clock, BadgeCheck, ChevronRight, Wrench } from "lucide-react";

const categories = [
  { icon: FlaskConical, name: "Chemicals", slug: "chemicals", color: "from-purple-500 to-purple-600" },
  { icon: Wrench, name: "Tools", slug: "tools", color: "from-orange-500 to-orange-600" },
  { icon: Paintbrush, name: "Paints", slug: "paints", color: "from-pink-500 to-pink-600" },
  { icon: Zap, name: "Electrical", slug: "electrical", color: "from-yellow-500 to-yellow-600" },
  { icon: Droplets, name: "Plumbing", slug: "plumbing", color: "from-cyan-500 to-cyan-600" },
  { icon: Shield, name: "Safety", slug: "safety_equipment", color: "from-red-500 to-red-600" },
];

const features = [
  { icon: Truck, title: "Fast Delivery", description: "Island-wide delivery within 2-3 days" },
  { icon: BadgeCheck, title: "Quality Guaranteed", description: "100% genuine products" },
  { icon: Clock, title: "24/7 Support", description: "Always here to help you" },
];

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await productActions.getAll(0, 8);
        setProducts(response.products);
      } catch (error) {
        console.error("Failed to fetch products:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchProducts();
  }, []);

  const refreshProducts = async () => {
    const response = await productActions.getAll(0, 8);
    setProducts(response.products);
  };

  return (
    <CustomerLayout>
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-background via-background to-orange-950/20">
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-5" />
        <div className="container mx-auto px-4 py-20 md:py-32 relative">
          <div className="max-w-3xl">
            <Badge className="mb-4 bg-orange-500/10 text-orange-400 border-orange-500/30">Premium Hardware Store</Badge>
            <h1 className="text-4xl md:text-6xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-foreground via-foreground to-orange-400">
              Quality Chemicals & Hardware for Every Project
            </h1>
            <p className="text-xl text-muted-foreground mb-8 max-w-2xl">
              Your one-stop shop for professional-grade chemicals, tools, paints, and building materials. Serving contractors and DIY enthusiasts across Sri Lanka.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link href="/products">
                <Button size="lg" className="gap-2 bg-orange-500 hover:bg-orange-600 text-white shadow-lg shadow-orange-500/25">
                  Browse Products
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <Link href="/quotations">
                <Button size="lg" variant="outline" className="gap-2 border-orange-500/50 text-orange-400 hover:bg-orange-500/10">
                  Request Quote
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Categories Section */}
      <section className="py-16 bg-card/30">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold mb-2">Shop by Category</h2>
              <p className="text-muted-foreground">Find exactly what you need</p>
            </div>
            <Link href="/products">
              <Button variant="ghost" className="gap-2 text-orange-400 hover:text-orange-300">
                View All <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {categories.map((category) => {
              const Icon = category.icon;
              return (
                <Link key={category.slug} href={`/products?category=${category.slug}`}>
                  <Card className="group cursor-pointer bg-card/50 border-border/50 hover:border-orange-500/50 transition-all duration-300 hover:shadow-lg hover:shadow-orange-500/5">
                    <CardContent className="flex flex-col items-center justify-center p-6 text-center">
                      <div className={`p-4 rounded-2xl bg-gradient-to-br ${category.color} mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className="h-6 w-6 text-white" />
                      </div>
                      <span className="font-medium text-sm group-hover:text-orange-400 transition-colors">{category.name}</span>
                    </CardContent>
                  </Card>
                </Link>
              );
            })}
          </div>
        </div>
      </section>

      {/* Featured Products Section */}
      <section className="py-16">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold mb-2">Featured Products</h2>
              <p className="text-muted-foreground">Top picks for your projects</p>
            </div>
            <Link href="/products">
              <Button variant="ghost" className="gap-2 text-orange-400 hover:text-orange-300">
                View All <ChevronRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>

          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Spinner className="h-8 w-8" />
            </div>
          ) : products.length > 0 ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {products.slice(0, 4).map((product) => (
                <ProductCard key={product.id} product={product} onAddToCart={refreshProducts} />
              ))}
            </div>
          ) : (
            <div className="text-center py-12 text-muted-foreground">
              <p>No products available at the moment.</p>
              <Link href="/products">
                <Button variant="outline" className="mt-4">
                  Browse All Products
                </Button>
              </Link>
            </div>
          )}
        </div>
      </section>

      {/* Features Section */}
      <section className="py-16 bg-gradient-to-b from-card/30 to-background">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {features.map((feature) => {
              const Icon = feature.icon;
              return (
                <div key={feature.title} className="flex items-start gap-4 p-6 rounded-2xl bg-card/50 border border-border/50">
                  <div className="p-3 rounded-xl bg-orange-500/10">
                    <Icon className="h-6 w-6 text-orange-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold mb-1">{feature.title}</h3>
                    <p className="text-sm text-muted-foreground">{feature.description}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-orange-600 to-orange-500">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">Ready to Start Your Project?</h2>
          <p className="text-lg text-white/80 mb-8 max-w-2xl mx-auto">Browse our extensive catalog or request a custom quote for bulk orders</p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link href="/products">
              <Button size="lg" variant="secondary" className="gap-2">
                Browse Catalog
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
            <Link href="/quotations">
              <Button size="lg" variant="outline" className="gap-2 bg-transparent border-white text-white hover:bg-white/10">
                Get Quote
              </Button>
            </Link>
          </div>
        </div>
      </section>
    </CustomerLayout>
  );
}
