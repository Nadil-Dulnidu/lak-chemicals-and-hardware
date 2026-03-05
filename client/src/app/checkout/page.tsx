"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { CustomerLayout } from "@/components/layouts/customer-layout";
import { cartActions, orderActions, paymentActions, quotationActions } from "@/lib/actions";
import { Cart, Quotation, CartItem, QuotationItem } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { ShoppingCart, ArrowLeft, Package, CreditCard, Banknote, Building2, CheckCircle, Shield, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@clerk/nextjs";

type PaymentMethod = "cash" | "card" | "bank";

function CheckoutContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const quotationId = searchParams.get("quotationId");

  const [cart, setCart] = useState<Cart | null>(null);
  const [quotation, setQuotation] = useState<Quotation | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState<PaymentMethod>("cash");
  const [notes, setNotes] = useState("");
  const [shippingAddress, setShippingAddress] = useState({
    name: "",
    phone: "",
    address: "",
    city: "",
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

  const fetchData = useCallback(async () => {
    if (!authToken) return;
    setIsLoading(true);
    try {
      if (quotationId) {
        // Fetch Quotation
        const qId = parseInt(quotationId);
        if (isNaN(qId)) throw new Error("Invalid quotation ID");
        const response = await quotationActions.getById(qId, authToken);
        setQuotation(response);
      } else {
        // Fetch Cart
        const response = await cartActions.get(authToken);
        setCart(response);
      }
    } catch (error) {
      console.error(error);
      toast.error("Failed to load checkout details");
      setCart(null);
      setQuotation(null);
    } finally {
      setIsLoading(false);
    }
  }, [authToken, quotationId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Prevent double submission
    if (isProcessing) return;

    // Validate data availability
    if (!cart && !quotation) return;

    // Validate shipping info
    if (!shippingAddress.name || !shippingAddress.phone || !shippingAddress.address) {
      toast.error("Please fill in all required shipping fields");
      return;
    }

    setIsProcessing(true);

    try {
      let orderId: number;

      if (quotation) {
        // Create order from quotation
        // Note: modify quotationActions.createOrder to return the created order
        const createdOrder = await quotationActions.createOrder(
          quotation.quotation_id,
          {
            payment_method: selectedPayment === "cash" ? "Cash on Delivery" : selectedPayment === "card" ? "Card" : "Bank Transfer",
            notes: notes,
            customer_name: shippingAddress.name,
            phone: shippingAddress.phone,
            address: shippingAddress.address,
            city: shippingAddress.city || undefined,
          },
          authToken,
        );

        orderId = createdOrder.order_id;
      } else if (cart) {
        // Create order from cart (new API: pass cart_id, items resolved server-side)
        const order = await orderActions.createFromCart(
          {
            cart_id: cart.cart_id,
            payment_method: selectedPayment === "cash" ? "Cash on Delivery" : selectedPayment === "card" ? "Card" : "Bank Transfer",
            notes: notes || undefined,
            customer_name: shippingAddress.name,
            phone: shippingAddress.phone,
            address: shippingAddress.address,
            city: shippingAddress.city || undefined,
          },
          authToken,
        );
        orderId = order.order_id;

        // Clear cart
        await cartActions.clear(authToken);
      } else {
        throw new Error("No cart or quotation to process");
      }

      // If card payment, redirect to Stripe
      if (selectedPayment === "card") {
        try {
          const checkout = await paymentActions.createCheckout(orderId, authToken);
          if (checkout.checkout_url) {
            window.location.href = checkout.checkout_url;
            return;
          }
        } catch (error) {
          console.error(error);
          // If Stripe fails, still keep the order
          toast.error("Card payment unavailable. Order placed for cash payment.");
        }
      }

      toast.success("Order placed successfully!");
      router.push("/orders");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to place order");
    } finally {
      setIsProcessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto px-4 py-8 flex justify-center items-center min-h-[60vh]">
        <Spinner className="h-8 w-8" />
      </div>
    );
  }

  if ((!cart || cart.items.length === 0) && !quotation) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
          <ShoppingCart className="h-20 w-20 text-muted-foreground/30 mb-6" />
          <h1 className="text-2xl font-bold mb-2">Nothing to checkout</h1>
          <p className="text-muted-foreground mb-6">Add products to cart or request a quotation</p>
          <Link href="/products">
            <Button className="gap-2 bg-orange-500 hover:bg-orange-600">Browse Products</Button>
          </Link>
        </div>
      </div>
    );
  }

  // Determine items and totals to display
  const items: (CartItem | QuotationItem)[] = quotation ? quotation.items : cart?.items || [];
  const subtotal = quotation ? quotation.total_amount : cart?.total_amount || 0;
  const discount = quotation?.discount_amount || 0;
  const total = subtotal - discount;

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <Link href={quotation ? "/quotations" : "/cart"} className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors mb-4">
          <ArrowLeft className="h-4 w-4" />
          {quotation ? "Back to Quotations" : "Back to Cart"}
        </Link>
        <h1 className="text-3xl font-bold">{quotation ? `Checkout Quotation #${quotation.quotation_id}` : "Checkout"}</h1>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Checkout Form */}
          <div className="lg:col-span-2 space-y-6">
            {/* Shipping Information */}
            <Card className="bg-card/50 border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Shipping Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Full Name <span className="text-destructive">*</span>
                    </label>
                    <Input value={shippingAddress.name} onChange={(e) => setShippingAddress({ ...shippingAddress, name: e.target.value })} placeholder="John Doe" required />
                  </div>
                  <div>
                    <label className="text-sm font-medium mb-2 block">
                      Phone Number <span className="text-destructive">*</span>
                    </label>
                    <Input value={shippingAddress.phone} onChange={(e) => setShippingAddress({ ...shippingAddress, phone: e.target.value })} placeholder="+94 XX XXX XXXX" required />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">
                    Address <span className="text-destructive">*</span>
                  </label>
                  <Input value={shippingAddress.address} onChange={(e) => setShippingAddress({ ...shippingAddress, address: e.target.value })} placeholder="Street address" required />
                </div>
                <div>
                  <label className="text-sm font-medium mb-2 block">City</label>
                  <Input value={shippingAddress.city} onChange={(e) => setShippingAddress({ ...shippingAddress, city: e.target.value })} placeholder="City" />
                </div>
              </CardContent>
            </Card>

            {/* Payment Method */}
            <Card className="bg-card/50 border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Payment Method</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Cash on Delivery */}
                <div
                  className={cn("p-4 rounded-lg border-2 cursor-pointer transition-all", selectedPayment === "cash" ? "border-orange-500 bg-orange-500/10" : "border-border/50 hover:border-border")}
                  onClick={() => setSelectedPayment("cash")}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center", selectedPayment === "cash" ? "border-orange-500" : "border-muted-foreground")}>
                      {selectedPayment === "cash" && <div className="w-3 h-3 rounded-full bg-orange-500" />}
                    </div>
                    <Banknote className="h-5 w-5 text-green-400" />
                    <div className="flex-1">
                      <p className="font-medium">Cash on Delivery</p>
                      <p className="text-sm text-muted-foreground">Pay when your order arrives</p>
                    </div>
                    <Badge className="bg-green-500/10 text-green-400 border-green-500/30">Popular</Badge>
                  </div>
                </div>

                {/* Card Payment */}
                <div
                  className={cn("p-4 rounded-lg border-2 cursor-pointer transition-all", selectedPayment === "card" ? "border-orange-500 bg-orange-500/10" : "border-border/50 hover:border-border")}
                  onClick={() => setSelectedPayment("card")}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center", selectedPayment === "card" ? "border-orange-500" : "border-muted-foreground")}>
                      {selectedPayment === "card" && <div className="w-3 h-3 rounded-full bg-orange-500" />}
                    </div>
                    <CreditCard className="h-5 w-5 text-blue-400" />
                    <div className="flex-1">
                      <p className="font-medium">Credit/Debit Card</p>
                      <p className="text-sm text-muted-foreground">Secure payment via Stripe</p>
                    </div>
                    <div className="flex items-center gap-1">
                      <Lock className="h-4 w-4 text-muted-foreground" />
                    </div>
                  </div>
                </div>

                {/* Bank Transfer */}
                <div
                  className={cn("p-4 rounded-lg border-2 cursor-pointer transition-all", selectedPayment === "bank" ? "border-orange-500 bg-orange-500/10" : "border-border/50 hover:border-border")}
                  onClick={() => setSelectedPayment("bank")}
                >
                  <div className="flex items-center gap-3">
                    <div className={cn("w-5 h-5 rounded-full border-2 flex items-center justify-center", selectedPayment === "bank" ? "border-orange-500" : "border-muted-foreground")}>
                      {selectedPayment === "bank" && <div className="w-3 h-3 rounded-full bg-orange-500" />}
                    </div>
                    <Building2 className="h-5 w-5 text-purple-400" />
                    <div className="flex-1">
                      <p className="font-medium">Bank Transfer</p>
                      <p className="text-sm text-muted-foreground">Transfer to our bank account</p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Order Notes */}
            <Card className="bg-card/50 border-border/50">
              <CardHeader>
                <CardTitle className="text-lg">Order Notes (Optional)</CardTitle>
              </CardHeader>
              <CardContent>
                <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Any special instructions for your order..." className="min-h-25" />
              </CardContent>
            </Card>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <Card className="bg-card/50 border-border/50 sticky top-24">
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Items */}
                <div className="space-y-3 max-h-60 overflow-y-auto scrollbar-thin">
                  {items.map((item) => (
                    <div key={item.product_id} className="flex gap-3">
                      <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center shrink-0">
                        <Package className="h-5 w-5 text-muted-foreground/30" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{item.product_name}</p>
                        <p className="text-xs text-muted-foreground">Qty: {item.quantity}</p>
                      </div>
                      <p className="text-sm font-medium">LKR {item.subtotal.toLocaleString()}</p>
                    </div>
                  ))}
                </div>

                <Separator />

                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Subtotal</span>
                    <span>LKR {subtotal.toLocaleString()}</span>
                  </div>
                  {quotation && discount > 0 && (
                    <div className="flex justify-between text-sm text-green-400">
                      <span>Discount</span>
                      <span>- LKR {discount.toLocaleString()}</span>
                    </div>
                  )}
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Shipping</span>
                    <span className="text-green-400">Free</span>
                  </div>
                </div>

                <Separator />

                <div className="flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>LKR {total.toLocaleString()}</span>
                </div>

                {/* Place Order Button */}
                <Button type="submit" className="w-full gap-2 bg-orange-500 hover:bg-orange-600 h-12 text-base" disabled={isProcessing}>
                  {isProcessing ? (
                    <>
                      <Spinner className="h-4 w-4" />
                      Processing...
                    </>
                  ) : selectedPayment === "card" ? (
                    <>
                      <CreditCard className="h-5 w-5" />
                      Pay Now - LKR {total.toLocaleString()}
                    </>
                  ) : (
                    <>
                      <CheckCircle className="h-5 w-5" />
                      Place Order
                    </>
                  )}
                </Button>

                {/* Security Badge */}
                <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground pt-2">
                  <Shield className="h-4 w-4" />
                  <span>Secure checkout</span>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </form>
    </div>
  );
}

export default function CheckoutPage() {
  return (
    <CustomerLayout>
      <Suspense
        fallback={
          <div className="container mx-auto px-4 py-8 flex justify-center items-center min-h-[60vh]">
            <Spinner className="h-8 w-8" />
          </div>
        }
      >
        <CheckoutContent />
      </Suspense>
    </CustomerLayout>
  );
}
