"use client";

import { Suspense } from "react";
import { CustomerLayout } from "@/components/layouts/customer-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { CheckCircle, ArrowRight, Package, ShieldCheck, Sparkles } from "lucide-react";

function PaymentSuccessContent() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order_id");

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-lg mx-auto text-center">
        {/* Animated Success Icon */}
        <div className="relative mb-8">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-32 h-32 rounded-full bg-green-500/10 animate-ping" />
          </div>
          <div className="relative flex items-center justify-center">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-lg shadow-green-500/25">
              <CheckCircle className="h-12 w-12 text-white" />
            </div>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold mb-3">
          Payment Successful! <Sparkles className="inline h-7 w-7 text-orange-400" />
        </h1>
        <p className="text-muted-foreground text-lg mb-8">Your payment has been processed successfully. Thank you for shopping with us!</p>

        {/* Order Details Card */}
        <Card className="bg-card/50 border-border/50 mb-8">
          <CardContent className="pt-6 space-y-4">
            {orderId && (
              <div className="flex items-center justify-between">
                <span className="text-muted-foreground">Order ID</span>
                <span className="font-bold text-lg">#{orderId}</span>
              </div>
            )}
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Payment Status</span>
              <span className="inline-flex items-center gap-1.5 text-green-400 font-medium">
                <ShieldCheck className="h-4 w-4" />
                Confirmed
              </span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Payment Method</span>
              <span className="font-medium">Credit/Debit Card</span>
            </div>
          </CardContent>
        </Card>

        {/* Info Box */}
        <div className="bg-green-500/5 border border-green-500/20 rounded-xl p-4 mb-8">
          <p className="text-sm text-green-300">A confirmation email will be sent to your registered email address. You can track your order status from the orders page.</p>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link href="/orders">
            <Button className="w-full sm:w-auto gap-2 bg-orange-500 hover:bg-orange-600 h-11 px-6">
              <Package className="h-4 w-4" />
              View My Orders
            </Button>
          </Link>
          <Link href="/products">
            <Button variant="outline" className="w-full sm:w-auto gap-2 h-11 px-6 border-border/50 hover:bg-muted">
              Continue Shopping
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function PaymentSuccessPage() {
  return (
    <CustomerLayout>
      <Suspense
        fallback={
          <div className="container mx-auto px-4 py-12 flex justify-center items-center min-h-[60vh]">
            <Spinner className="h-8 w-8" />
          </div>
        }
      >
        <PaymentSuccessContent />
      </Suspense>
    </CustomerLayout>
  );
}
