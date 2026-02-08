"use client";

import { useEffect, useState, useCallback } from "react";
import { CustomerLayout } from "@/components/layouts/customer-layout";
import { cartActions, quotationActions, orderActions } from "@/lib/actions";
import { Cart } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Trash2, Plus, Minus, ShoppingCart, FileText, ArrowRight, Package, CreditCard, ShoppingBag } from "lucide-react";

export default function CartPage() {
  const router = useRouter();
  const [cart, setCart] = useState<Cart | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [updatingItems, setUpdatingItems] = useState<Set<number>>(new Set());
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);
  const [isRequestingQuote, setIsRequestingQuote] = useState(false);

  const fetchCart = useCallback(async () => {
    try {
      const response = await cartActions.get();
      setCart(response);
    } catch (error) {
      // Cart might not exist yet
      setCart(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const updateQuantity = async (cartItemId: number, newQuantity: number) => {
    if (newQuantity < 1) return;

    setUpdatingItems((prev) => new Set(prev).add(cartItemId));
    try {
      const response = await cartActions.updateItem(cartItemId, { quantity: newQuantity });
      setCart(response);
      toast.success("Cart updated");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to update cart");
    } finally {
      setUpdatingItems((prev) => {
        const newSet = new Set(prev);
        newSet.delete(cartItemId);
        return newSet;
      });
    }
  };

  const removeItem = async (cartItemId: number) => {
    setUpdatingItems((prev) => new Set(prev).add(cartItemId));
    try {
      await cartActions.removeItem(cartItemId);
      await fetchCart();
      toast.success("Item removed from cart");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to remove item");
    } finally {
      setUpdatingItems((prev) => {
        const newSet = new Set(prev);
        newSet.delete(cartItemId);
        return newSet;
      });
    }
  };

  const clearCart = async () => {
    try {
      await cartActions.clear();
      setCart(null);
      toast.success("Cart cleared");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to clear cart");
    }
  };

  const requestQuotation = async () => {
    setIsRequestingQuote(true);
    try {
      await quotationActions.createFromCart({ notes: "" });
      await cartActions.clear();
      setCart(null);
      toast.success("Quotation request submitted! We'll review and get back to you.");
      router.push("/quotations");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to create quotation");
    } finally {
      setIsRequestingQuote(false);
    }
  };

  const placeOrder = async () => {
    if (!cart) return;

    setIsPlacingOrder(true);
    try {
      // Create order directly from cart items
      const orderItems = cart.items.map((item) => ({
        product_id: item.product_id,
        quantity: item.quantity,
      }));

      await orderActions.create({
        items: orderItems,
        payment_method: "Cash on Delivery",
        notes: "",
      });

      // Clear the cart after order is placed
      await cartActions.clear();
      setCart(null);
      toast.success("Order placed successfully!");
      router.push("/orders");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Failed to place order");
    } finally {
      setIsPlacingOrder(false);
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

  if (!cart || cart.items.length === 0) {
    return (
      <CustomerLayout>
        <div className="container mx-auto px-4 py-8">
          <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
            <ShoppingCart className="h-20 w-20 text-muted-foreground/30 mb-6" />
            <h1 className="text-2xl font-bold mb-2">Your cart is empty</h1>
            <p className="text-muted-foreground mb-6">Add some products to get started</p>
            <Link href="/products">
              <Button className="gap-2 bg-orange-500 hover:bg-orange-600">
                Browse Products
                <ArrowRight className="h-4 w-4" />
              </Button>
            </Link>
          </div>
        </div>
      </CustomerLayout>
    );
  }

  return (
    <CustomerLayout>
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold mb-2">Shopping Cart</h1>
            <p className="text-muted-foreground">
              {cart.total_items} {cart.total_items === 1 ? "item" : "items"} in your cart
            </p>
          </div>
          <Button variant="outline" onClick={clearCart} className="gap-2 text-destructive">
            <Trash2 className="h-4 w-4" />
            Clear Cart
          </Button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Cart Items */}
          <div className="lg:col-span-2 space-y-4">
            {cart.items.map((item) => (
              <Card key={item.cart_item_id} className="bg-card/50 border-border/50">
                <CardContent className="p-4">
                  <div className="flex gap-4">
                    {/* Product Image */}
                    <Link href={`/products/${item.product_id}`} className="flex-shrink-0">
                      <div className="w-24 h-24 rounded-lg bg-muted flex items-center justify-center hover:bg-muted/80 transition-colors">
                        <Package className="h-8 w-8 text-muted-foreground/30" />
                      </div>
                    </Link>

                    {/* Product Details */}
                    <div className="flex-1 min-w-0">
                      <Link href={`/products/${item.product_id}`}>
                        <h3 className="font-semibold text-lg mb-1 hover:text-orange-400 transition-colors">{item.product_name}</h3>
                      </Link>
                      <p className="text-muted-foreground text-sm mb-2">LKR {item.unit_price} each</p>

                      {/* Quantity Controls */}
                      <div className="flex items-center gap-2">
                        <Button
                          variant="outline"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => updateQuantity(item.cart_item_id, item.quantity - 1)}
                          disabled={updatingItems.has(item.cart_item_id) || item.quantity <= 1}
                        >
                          <Minus className="h-4 w-4" />
                        </Button>
                        <Input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => updateQuantity(item.cart_item_id, parseInt(e.target.value) || 1)}
                          className="w-16 h-8 text-center"
                          min={1}
                          disabled={updatingItems.has(item.cart_item_id)}
                        />
                        <Button variant="outline" size="icon" className="h-8 w-8" onClick={() => updateQuantity(item.cart_item_id, item.quantity + 1)} disabled={updatingItems.has(item.cart_item_id)}>
                          <Plus className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>

                    {/* Item Total & Remove */}
                    <div className="text-right flex flex-col items-end">
                      <p className="font-bold text-lg">LKR {item.subtotal.toLocaleString()}</p>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-destructive hover:text-destructive mt-2"
                        onClick={() => removeItem(item.cart_item_id)}
                        disabled={updatingItems.has(item.cart_item_id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <Card className="bg-card/50 border-border/50 sticky top-24">
              <CardHeader>
                <CardTitle>Order Summary</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Subtotal ({cart.total_items} items)</span>
                  <span>LKR {cart.total_amount.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-muted-foreground">Shipping</span>
                  <span className="text-green-400">Free</span>
                </div>
                <Separator />
                <div className="flex justify-between font-bold text-lg">
                  <span>Total</span>
                  <span>LKR {cart.total_amount.toLocaleString()}</span>
                </div>
              </CardContent>
              <CardFooter className="flex flex-col gap-3">
                {/* Direct Place Order Button */}
                <Button className="w-full gap-2 bg-orange-500 hover:bg-orange-600 h-12 text-base" onClick={placeOrder} disabled={isPlacingOrder || isRequestingQuote}>
                  {isPlacingOrder ? (
                    <>
                      <Spinner className="h-4 w-4" />
                      Placing Order...
                    </>
                  ) : (
                    <>
                      <ShoppingBag className="h-5 w-5" />
                      Place Order
                    </>
                  )}
                </Button>

                {/* Checkout Button (for future payment integration) */}
                <Link href="/checkout" className="w-full">
                  <Button variant="outline" className="w-full gap-2 border-orange-500/50 text-orange-400 hover:bg-orange-500/10" disabled={isPlacingOrder || isRequestingQuote}>
                    <CreditCard className="h-4 w-4" />
                    Checkout with Payment
                  </Button>
                </Link>

                <div className="relative w-full">
                  <Separator className="my-2" />
                  <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-2 text-xs text-muted-foreground">or</span>
                </div>

                {/* Request Quotation Option */}
                <Button variant="ghost" className="w-full gap-2 text-muted-foreground hover:text-foreground" onClick={requestQuotation} disabled={isPlacingOrder || isRequestingQuote}>
                  {isRequestingQuote ? (
                    <>
                      <Spinner className="h-4 w-4" />
                      Requesting...
                    </>
                  ) : (
                    <>
                      <FileText className="h-4 w-4" />
                      Request Quotation Instead
                    </>
                  )}
                </Button>

                <Link href="/products" className="w-full">
                  <Button variant="link" className="w-full text-muted-foreground">
                    Continue Shopping
                  </Button>
                </Link>
              </CardFooter>
            </Card>

            {/* Payment Info */}
            <Card className="bg-card/50 border-border/50 mt-4">
              <CardContent className="p-4">
                <h4 className="font-medium mb-3 text-sm">We Accept</h4>
                <div className="flex gap-2 flex-wrap">
                  <div className="px-3 py-1.5 rounded bg-muted text-xs font-medium">Cash on Delivery</div>
                  <div className="px-3 py-1.5 rounded bg-muted text-xs font-medium">Bank Transfer</div>
                  <div className="px-3 py-1.5 rounded bg-muted text-xs font-medium">Card Payment</div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </CustomerLayout>
  );
}
