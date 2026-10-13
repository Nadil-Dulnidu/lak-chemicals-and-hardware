package com.lakchemicals.business.controller;

import com.lakchemicals.business.dto.cart.*;
import com.lakchemicals.business.security.SecurityUtils;
import com.lakchemicals.business.service.CartService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@Slf4j
@RestController
@RequestMapping({"/api/v1/cart", "/cart"})
@Tag(name = "Cart", description = "Shopping Cart Endpoints")
@RequiredArgsConstructor
public class CartController {

    private final CartService cartService;

    @PostMapping("/items")
    @Operation(summary = "Add an item to the shopping cart")
    public ResponseEntity<CartResponse> addItem(@Valid @RequestBody AddToCartRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(cartService.addItemToCart(userId, request));
    }

    @GetMapping
    @Operation(summary = "Get the current user's cart")
    public ResponseEntity<CartResponse> getCart() {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(cartService.getCart(userId));
    }

    @PutMapping("/items/{product_id}")
    @Operation(summary = "Update an item quantity in the cart")
    public ResponseEntity<CartResponse> updateItem(
            @PathVariable("product_id") UUID productId,
            @Valid @RequestBody UpdateCartItemRequest request
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(cartService.updateItemQuantity(userId, productId, request.getQuantity()));
    }

    @DeleteMapping("/items/{product_id}")
    @Operation(summary = "Remove an item from the cart")
    public ResponseEntity<CartResponse> removeItem(@PathVariable("product_id") UUID productId) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(cartService.removeItemFromCart(userId, productId));
    }

    @DeleteMapping
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Clear all items from the cart")
    public ResponseEntity<Void> clearCart() {
        String userId = SecurityUtils.getCurrentUserId();
        cartService.clearCart(userId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/summary")
    @Operation(summary = "Get shopping cart summary (item count and total)")
    public ResponseEntity<CartSummaryResponse> getCartSummary() {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(cartService.getCartSummary(userId));
    }
}
