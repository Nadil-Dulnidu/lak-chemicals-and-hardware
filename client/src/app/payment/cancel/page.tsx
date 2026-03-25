"use client";

import { Suspense } from "react";
import { CustomerLayout } from "@/components/layouts/customer-layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Spinner } from "@/components/ui/spinner";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { XCircle, ArrowLeft, RotateCcw, HelpCircle, ShieldAlert } from "lucide-react";

function PaymentCancelContent() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order_id");

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-lg mx-auto text-center">
        {/* Animated Cancel Icon */}
        <div className="relative mb-8">
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="w-32 h-32 rounded-full bg-red-500/10 animate-pulse" />
          </div>
          <div className="relative flex items-center justify-center">
            <div className="w-24 h-24 rounded-full bg-gradient-to-br from-red-500 to-rose-600 flex items-center justify-center shadow-lg shadow-red-500/25">
              <XCircle className="h-12 w-12 text-white" />
            </div>
          </div>
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold mb-3">Payment Cancelled</h1>
        <p className="text-muted-foreground text-lg mb-8">Your payment was not processed. Don&apos;t worry — your order has been saved and no charges were made.</p>

        {/* Order Details Card */}
        <Card className="bg-card/50 border-border/50 mb-8">
          <CardContent className="pt-6 space-y-4">
            {orderId && (
              <>
                <div className="flex items-center justify-between">
                  <span className="text-muted-foreground">Order ID</span>
                  <span className="font-bold text-lg">#{orderId}</span>
                </div>
                <Separator />
              </>
            )}
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Payment Status</span>
              <span className="inline-flex items-center gap-1.5 text-red-400 font-medium">
                <ShieldAlert className="h-4 w-4" />
                Cancelled
              </span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Order Status</span>
              <span className="inline-flex items-center gap-1.5 text-yellow-400 font-medium">Pending Payment</span>
            </div>
          </CardContent>
        </Card>

        {/* Info Box */}
        <div className="bg-amber-500/5 border border-amber-500/20 rounded-xl p-4 mb-8">
          <div className="flex items-start gap-3">
            <HelpCircle className="h-5 w-5 text-amber-400 shrink-0 mt-0.5" />
            <p className="text-sm text-amber-200 text-left">Your order is still saved. You can try paying again from the orders page, or choose a different payment method like Cash on Delivery.</p>
          </div>
        </div>

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          {orderId ? (
            <Link href="/orders">
              <Button className="w-full sm:w-auto gap-2 bg-orange-500 hover:bg-orange-600 h-11 px-6">
                <RotateCcw className="h-4 w-4" />
                View My Orders
              </Button>
            </Link>
          ) : (
            <Link href="/checkout">
              <Button className="w-full sm:w-auto gap-2 bg-orange-500 hover:bg-orange-600 h-11 px-6">
                <RotateCcw className="h-4 w-4" />
                Try Again
              </Button>
            </Link>
          )}
          <Link href="/products">
            <Button variant="outline" className="w-full sm:w-auto gap-2 h-11 px-6 border-border/50 hover:bg-muted">
              <ArrowLeft className="h-4 w-4" />
              Back to Store
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function PaymentCancelPage() {
  return (
    <CustomerLayout>
      <Suspense
        fallback={
          <div className="container mx-auto px-4 py-12 flex justify-center items-center min-h-[60vh]">
            <Spinner className="h-8 w-8" />
          </div>
        }
      >
        <PaymentCancelContent />
      </Suspense>
    </CustomerLayout>
  );
}
