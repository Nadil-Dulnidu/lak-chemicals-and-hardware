package com.lakchemicals.business.service;

import com.lakchemicals.business.dto.cart.*;
import com.lakchemicals.business.entity.Cart;
import com.lakchemicals.business.entity.CartItem;
import com.lakchemicals.business.entity.Product;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.exception.ResourceNotFoundException;
import com.lakchemicals.business.repository.CartItemRepository;
import com.lakchemicals.business.repository.CartRepository;
import com.lakchemicals.business.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

@Slf4j
@Service
@RequiredArgsConstructor
public class CartService {

    private final CartRepository cartRepository;
    private final CartItemRepository cartItemRepository;
    private final ProductRepository productRepository;

    @Transactional
    public CartResponse addItemToCart(String userId, AddToCartRequest request) {
        log.info("Adding product {} (qty: {}) to cart for user {}", request.getProductId(), request.getQuantity(), userId);

        Product product = productRepository.findById(request.getProductId())
                .orElseThrow(() -> new ResourceNotFoundException("Product not found with id: " + request.getProductId()));

        if (!Boolean.TRUE.equals(product.getIsActive())) {
            throw new BadRequestException("Product is inactive and cannot be added to cart");
        }

        Cart cart = getOrCreateCart(userId);

        CartItem cartItem = cartItemRepository.findByCart_CartIdAndProduct_Id(cart.getCartId(), product.getId())
                .orElse(null);

        if (cartItem != null) {
            cartItem.setQuantity(cartItem.getQuantity() + request.getQuantity());
            cartItemRepository.save(cartItem);
        } else {
            cartItem = CartItem.builder()
                    .cart(cart)
                    .product(product)
                    .quantity(request.getQuantity())
                    .build();
            cartItemRepository.save(cartItem);
            cart.getCartItems().add(cartItem);
        }

        return getCart(userId);
    }

    @Transactional
    public CartResponse updateItemQuantity(String userId, UUID productId, int newQuantity) {
        return updateItemQuantityByIdentifier(userId, productId.toString(), newQuantity);
    }

    @Transactional
    public CartResponse updateItemQuantityByIdentifier(String userId, String itemOrProductId, int newQuantity) {
        Cart cart = getOrCreateCart(userId);
        CartItem cartItem = null;

        try {
            int itemId = Integer.parseInt(itemOrProductId);
            cartItem = cartItemRepository.findById(itemId)
                    .filter(ci -> ci.getCart().getCartId().equals(cart.getCartId()))
                    .orElse(null);
        } catch (NumberFormatException ignored) {}

        if (cartItem == null) {
            try {
                UUID prodId = UUID.fromString(itemOrProductId);
                cartItem = cartItemRepository.findByCart_CartIdAndProduct_Id(cart.getCartId(), prodId).orElse(null);
            } catch (IllegalArgumentException ignored) {}
        }

        if (cartItem == null) {
            throw new ResourceNotFoundException("Item not found in cart for identifier: " + itemOrProductId);
        }

        if (newQuantity <= 0) {
            cartItemRepository.delete(cartItem);
            cart.getCartItems().remove(cartItem);
        } else {
            cartItem.setQuantity(newQuantity);
            cartItemRepository.save(cartItem);
        }

        return getCart(userId);
    }

    @Transactional
    public CartResponse removeItemFromCart(String userId, UUID productId) {
        return removeItemFromCartByIdentifier(userId, productId.toString());
    }

    @Transactional
    public CartResponse removeItemFromCartByIdentifier(String userId, String itemOrProductId) {
        Cart cart = getOrCreateCart(userId);
        CartItem cartItem = null;

        try {
            int itemId = Integer.parseInt(itemOrProductId);
            cartItem = cartItemRepository.findById(itemId)
                    .filter(ci -> ci.getCart().getCartId().equals(cart.getCartId()))
                    .orElse(null);
        } catch (NumberFormatException ignored) {}

        if (cartItem == null) {
            try {
                UUID prodId = UUID.fromString(itemOrProductId);
                cartItem = cartItemRepository.findByCart_CartIdAndProduct_Id(cart.getCartId(), prodId).orElse(null);
            } catch (IllegalArgumentException ignored) {}
        }

        if (cartItem == null) {
            throw new ResourceNotFoundException("Item not found in cart for identifier: " + itemOrProductId);
        }

        cartItemRepository.delete(cartItem);
        cart.getCartItems().remove(cartItem);

        return getCart(userId);
    }

    @Transactional
    public CartResponse getCart(String userId) {
        Cart cart = getOrCreateCart(userId);
        List<CartItem> items = cartItemRepository.findByCart_CartId(cart.getCartId());

        List<CartItemResponse> itemResponses = new ArrayList<>();
        BigDecimal totalAmount = BigDecimal.ZERO;
        int totalQuantity = 0;

        for (CartItem item : items) {
            Product p = item.getProduct();
            BigDecimal price = BigDecimal.valueOf(p.getPrice());
            BigDecimal subtotal = price.multiply(BigDecimal.valueOf(item.getQuantity()));

            totalAmount = totalAmount.add(subtotal);
            totalQuantity += item.getQuantity();

            itemResponses.add(CartItemResponse.builder()
                    .cartItemId(item.getCartItemId())
                    .productId(p.getId())
                    .productName(p.getName())
                    .productPrice(price)
                    .quantity(item.getQuantity())
                    .subtotal(subtotal)
                    .build());
        }

        return CartResponse.builder()
                .cartId(cart.getCartId())
                .userId(userId)
                .items(itemResponses)
                .totalItems(totalQuantity)
                .totalAmount(totalAmount)
                .build();
    }

    @Transactional
    public void clearCart(String userId) {
        Cart cart = cartRepository.findByUserId(userId).orElse(null);
        if (cart != null) {
            cartItemRepository.deleteByCart_CartId(cart.getCartId());
            cart.getCartItems().clear();
        }
    }

    @Transactional(readOnly = true)
    public CartSummaryResponse getCartSummary(String userId) {
        Cart cart = cartRepository.findByUserId(userId).orElse(null);
        if (cart == null) {
            return CartSummaryResponse.builder()
                    .cartId(0)
                    .userId(userId)
                    .totalItems(0)
                    .totalAmount(BigDecimal.ZERO)
                    .build();
        }

        List<CartItem> items = cartItemRepository.findByCart_CartId(cart.getCartId());
        BigDecimal totalAmount = BigDecimal.ZERO;
        int totalQuantity = 0;

        for (CartItem item : items) {
            BigDecimal price = BigDecimal.valueOf(item.getProduct().getPrice());
            totalAmount = totalAmount.add(price.multiply(BigDecimal.valueOf(item.getQuantity())));
            totalQuantity += item.getQuantity();
        }

        return CartSummaryResponse.builder()
                .cartId(cart.getCartId())
                .userId(userId)
                .totalItems(totalQuantity)
                .totalAmount(totalAmount)
                .build();
    }

    private Cart getOrCreateCart(String userId) {
        return cartRepository.findByUserId(userId).orElseGet(() ->
                cartRepository.save(Cart.builder()
                        .userId(userId)
                        .build())
        );
    }
}
