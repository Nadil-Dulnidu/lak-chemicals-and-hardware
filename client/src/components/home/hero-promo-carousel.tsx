"use client";

import * as React from "react";
import Image from "next/image";
import Link from "next/link";
import Autoplay from "embla-carousel-autoplay";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Carousel,
  CarouselContent,
  CarouselItem,
  type CarouselApi,
} from "@/components/ui/carousel";
import { ArrowRight, Percent, Truck, Sparkles, FlaskConical } from "lucide-react";

interface PromoSlide {
  id: string;
  title: string;
  subtitle: string;
  badge: string;
  cta: string;
  href: string;
  image?: string;
  gradient: string;
  accentColor: string;
  icon: React.ElementType;
}

const promoSlides: PromoSlide[] = [
  {
    id: "power-tools",
    title: "Power Tools Sale",
    subtitle: "Up to 30% off on premium drills, grinders & more",
    badge: "Limited Time",
    cta: "Shop Now",
    href: "/products?category=tools",
    image: "/promos/power-tools.png",
    gradient: "from-orange-950/80 via-orange-900/40 to-transparent",
    accentColor: "orange",
    icon: Percent,
  },
  {
    id: "paints",
    title: "Premium Paints",
    subtitle: "New arrivals from top brands, vibrant colors",
    badge: "New Arrivals",
    cta: "Explore",
    href: "/products?category=paints",
    image: "/promos/paints.png",
    gradient: "from-pink-950/80 via-pink-900/40 to-transparent",
    accentColor: "pink",
    icon: Sparkles,
  },
  {
    id: "chemicals",
    title: "Industrial Chemicals",
    subtitle: "Trusted quality for professionals, bulk pricing available",
    badge: "Best Sellers",
    cta: "View Range",
    href: "/products?category=chemicals",
    gradient: "from-blue-950/90 via-indigo-900/60 to-purple-950/40",
    accentColor: "blue",
    icon: FlaskConical,
  },
  {
    id: "delivery",
    title: "Free Delivery",
    subtitle: "On all orders over Rs. 5,000 island-wide",
    badge: "Special Offer",
    cta: "Start Shopping",
    href: "/products",
    gradient: "from-emerald-950/90 via-green-900/60 to-teal-950/40",
    accentColor: "green",
    icon: Truck,
  },
];

const accentStyles: Record<string, { badge: string; button: string; dot: string; dotActive: string; iconBg: string }> = {
  orange: {
    badge: "bg-orange-500/20 text-orange-300 border-orange-500/40",
    button: "bg-orange-500 hover:bg-orange-600 text-white shadow-lg shadow-orange-500/30",
    dot: "bg-white/20 hover:bg-white/40",
    dotActive: "bg-orange-500",
    iconBg: "bg-orange-500/20",
  },
  pink: {
    badge: "bg-pink-500/20 text-pink-300 border-pink-500/40",
    button: "bg-pink-500 hover:bg-pink-600 text-white shadow-lg shadow-pink-500/30",
    dot: "bg-white/20 hover:bg-white/40",
    dotActive: "bg-pink-500",
    iconBg: "bg-pink-500/20",
  },
  blue: {
    badge: "bg-blue-500/20 text-blue-300 border-blue-500/40",
    button: "bg-blue-500 hover:bg-blue-600 text-white shadow-lg shadow-blue-500/30",
    dot: "bg-white/20 hover:bg-white/40",
    dotActive: "bg-blue-500",
    iconBg: "bg-blue-500/20",
  },
  green: {
    badge: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
    button: "bg-emerald-500 hover:bg-emerald-600 text-white shadow-lg shadow-emerald-500/30",
    dot: "bg-white/20 hover:bg-white/40",
    dotActive: "bg-emerald-500",
    iconBg: "bg-emerald-500/20",
  },
};

export function HeroPromoCarousel() {
  const [api, setApi] = React.useState<CarouselApi>();
  const [current, setCurrent] = React.useState(0);

  React.useEffect(() => {
    if (!api) return;

    setCurrent(api.selectedScrollSnap());
    api.on("select", () => {
      setCurrent(api.selectedScrollSnap());
    });
  }, [api]);

  const plugin = React.useRef(
    Autoplay({ delay: 4000, stopOnInteraction: true, stopOnMouseEnter: true })
  );

  const currentSlide = promoSlides[current];
  const styles = accentStyles[currentSlide?.accentColor || "orange"];

  return (
    <div className="relative w-full h-full rounded-2xl overflow-hidden border border-white/[0.06] shadow-2xl shadow-black/30 group">
      {/* Subtle shimmer effect on container */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/[0.04] via-transparent to-white/[0.02] pointer-events-none z-10" />

      <Carousel
        setApi={setApi}
        opts={{
          align: "start",
          loop: true,
        }}
        plugins={[plugin.current]}
        className="w-full h-full"
      >
        <CarouselContent className="h-full -ml-0">
          {promoSlides.map((slide) => {
            const Icon = slide.icon;
            const slideStyles = accentStyles[slide.accentColor];

            return (
              <CarouselItem key={slide.id} className="pl-0 h-full">
                <div className="relative w-full h-full min-h-[320px] md:min-h-[380px] overflow-hidden bg-gray-950">
                  {/* Background image */}
                  {slide.image ? (
                    <Image
                      src={slide.image}
                      alt={slide.title}
                      fill
                      className="object-cover object-center"
                      priority
                      sizes="(max-width: 768px) 100vw, 50vw"
                    />
                  ) : (
                    /* CSS gradient background for slides without images */
                    <div className={`absolute inset-0 bg-gradient-to-br ${slide.gradient}`} />
                  )}

                  {/* Gradient overlay for text readability */}
                  <div className={`absolute inset-0 bg-gradient-to-t ${slide.gradient}`} />
                  <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent" />

                  {/* Decorative elements for non-image slides */}
                  {!slide.image && (
                    <>
                      <div className="absolute top-8 right-8 opacity-10">
                        <Icon className="h-32 w-32 text-white" />
                      </div>
                      <div className="absolute bottom-12 right-16 opacity-5">
                        <Icon className="h-48 w-48 text-white -rotate-12" />
                      </div>
                      {/* Glow effect */}
                      <div className={`absolute top-1/2 right-1/4 w-64 h-64 rounded-full blur-[120px] opacity-20 ${
                        slide.accentColor === "blue" ? "bg-blue-500" :
                        slide.accentColor === "green" ? "bg-emerald-500" : "bg-orange-500"
                      }`} />
                    </>
                  )}

                  {/* Content */}
                  <div className="relative z-[5] flex flex-col justify-end h-full p-6 md:p-8">
                    <Badge className={`mb-3 w-fit text-xs font-medium ${slideStyles.badge}`}>
                      {slide.badge}
                    </Badge>
                    <h3 className="text-2xl md:text-3xl font-bold text-white mb-2 tracking-tight">
                      {slide.title}
                    </h3>
                    <p className="text-sm md:text-base text-white/70 mb-5 max-w-[280px] leading-relaxed">
                      {slide.subtitle}
                    </p>
                    <Link href={slide.href}>
                      <Button
                        size="sm"
                        className={`gap-2 ${slideStyles.button} transition-all duration-300 hover:scale-[1.03]`}
                      >
                        {slide.cta}
                        <ArrowRight className="h-3.5 w-3.5" />
                      </Button>
                    </Link>
                  </div>
                </div>
              </CarouselItem>
            );
          })}
        </CarouselContent>

        {/* Dot indicators */}
        <div className="absolute bottom-4 right-6 z-10 flex items-center gap-1.5">
          {promoSlides.map((slide, index) => (
            <button
              key={slide.id}
              onClick={() => api?.scrollTo(index)}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                index === current
                  ? `w-6 ${styles.dotActive}`
                  : `w-1.5 ${styles.dot}`
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      </Carousel>
    </div>
  );
}
