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
import { Paintbrush, Zap, Droplets, FlaskConical, Shield, ArrowRight, Truck, Clock, BadgeCheck, ChevronRight, Wrench, MessageCircle, Sparkles, Bot } from "lucide-react";
import { useAuth } from "@clerk/nextjs";
import { HeroPromoCarousel } from "@/components/home/hero-promo-carousel";

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

const aiFeatures = [
  { icon: MessageCircle, text: "Ask about your requirements" },
  { icon: Sparkles, text: "Get smart recommendations" },
  { icon: Bot, text: "Instant expert answers" },
];

export default function HomePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [authToken, setAuthToken] = useState<string | null>(null);
  const { getToken } = useAuth();

  useEffect(() => {
    const fetchToken = async () => {
      const token = await getToken({ template: "lak-chemicles-and-hardware" });
      setAuthToken(token);
    };
    fetchToken();
  }, [getToken]);

  console.log("Auth Token:", authToken);

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
        <div className="container mx-auto px-4 py-16 md:py-24 relative">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-10 lg:gap-12 items-center">
            {/* Left: Hero Text */}
            <div>
              <Badge className="mb-4 bg-orange-500/10 text-orange-400 border-orange-500/30">Premium Hardware Store</Badge>
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold mb-6 bg-clip-text text-transparent bg-gradient-to-r from-foreground via-foreground to-orange-400">
                Quality Chemicals & Hardware for Every Project
              </h1>
              <p className="text-lg md:text-xl text-muted-foreground mb-8 max-w-2xl">
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

            {/* Right: Promo Carousel */}
            <div className="w-full">
              <HeroPromoCarousel />
            </div>
          </div>
        </div>
      </section>

      {/* AI Chat Assistant CTA Section */}
      <section className="relative overflow-hidden py-14 md:py-16">
        {/* Multi-layer gradient background — orange theme */}
        <div className="absolute inset-0 bg-gradient-to-r from-orange-950/90 via-amber-950/80 to-orange-950/90" />
        <div className="absolute inset-0 bg-gradient-to-b from-black/30 via-transparent to-black/30" />

        {/* Animated glow orbs */}
        <div className="absolute top-1/2 left-1/4 -translate-y-1/2 w-72 h-72 bg-orange-500/15 rounded-full blur-[100px] animate-pulse" />
        <div className="absolute top-1/2 right-1/4 -translate-y-1/2 w-56 h-56 bg-amber-500/15 rounded-full blur-[80px] animate-pulse [animation-delay:1s]" />
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-96 h-32 bg-orange-500/10 rounded-full blur-[60px]" />

        {/* Subtle grid overlay */}
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-[0.03]" />

        <div className="container mx-auto px-4 relative z-10">
          <div className="flex flex-col md:flex-row items-center gap-8 md:gap-12">
            {/* Left: Icon + Content */}
            <div className="flex-1 text-center md:text-left">
              {/* Floating AI icon */}
              <div className="inline-flex items-center justify-center mb-5">
                <div className="relative">
                  <div className="absolute inset-0 bg-gradient-to-br from-orange-500 to-amber-600 rounded-2xl blur-lg opacity-50 animate-pulse" />
                  <div className="relative p-4 bg-gradient-to-br from-orange-500 to-amber-600 rounded-2xl shadow-xl shadow-orange-500/25">
                    <Bot className="h-8 w-8 text-white" />
                  </div>
                </div>
              </div>

              <Badge className="mb-3 bg-orange-500/15 text-orange-300 border-orange-500/30 text-xs font-medium">
                <Sparkles className="h-3 w-3 mr-1" />
                AI-Powered • New Feature
              </Badge>

              <h2 className="text-2xl md:text-3xl lg:text-4xl font-bold text-white mb-3 tracking-tight">Meet Your AI Product Assistant</h2>
              <p className="text-base md:text-lg text-white/60 max-w-xl mb-6">
                Not sure what you need? Chat with our intelligent assistant for instant product recommendations, comparisons, and expert advice - available 24/7.
              </p>

              {/* Feature pills */}
              <div className="flex flex-wrap gap-3 justify-center md:justify-start mb-6">
                {aiFeatures.map((feature) => {
                  const Icon = feature.icon;
                  return (
                    <div key={feature.text} className="flex items-center gap-2 px-3.5 py-2 rounded-full bg-white/6 border border-white/8 backdrop-blur-sm text-sm text-white/80">
                      <Icon className="h-3.5 w-3.5 text-orange-400" />
                      {feature.text}
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Right: CTA */}
            <div className="shrink-0">
              <Link href="/chat">
                <Button
                  size="lg"
                  className="gap-2.5 bg-gradient-to-r from-orange-500 to-amber-500 hover:from-orange-600 hover:to-amber-600 text-white shadow-xl shadow-orange-500/25 px-8 py-6 text-base font-semibold rounded-xl transition-all duration-300 hover:scale-[1.03] hover:shadow-orange-500/40"
                >
                  <MessageCircle className="h-5 w-5" />
                  Start a Conversation
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </Link>
              <p className="text-xs text-white/40 text-center mt-3">Free • Sign-up required</p>
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
      {/* <section className="py-20 bg-gradient-to-r from-orange-600 to-orange-500">
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
      </section> */}
    </CustomerLayout>
  );
}
