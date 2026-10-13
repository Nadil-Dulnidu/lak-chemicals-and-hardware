package com.lakchemicals.business;

import com.lakchemicals.business.dto.cart.*;
import com.lakchemicals.business.entity.Cart;
import com.lakchemicals.business.entity.CartItem;
import com.lakchemicals.business.entity.Product;
import com.lakchemicals.business.repository.CartItemRepository;
import com.lakchemicals.business.repository.CartRepository;
import com.lakchemicals.business.repository.ProductRepository;
import com.lakchemicals.business.service.CartService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class CartServiceTest {

    @Mock
    private CartRepository cartRepository;

    @Mock
    private CartItemRepository cartItemRepository;

    @Mock
    private ProductRepository productRepository;

    @InjectMocks
    private CartService cartService;

    private Cart cart;
    private Product product;
    private UUID productId;
    private String userId = "user_123";

    @BeforeEach
    void setUp() {
        productId = UUID.randomUUID();
        cart = Cart.builder()
                .cartId(1)
                .userId(userId)
                .cartItems(new ArrayList<>())
                .build();

        product = Product.builder()
                .id(productId)
                .name("Hammer")
                .price(1500.0)
                .stockQty(50)
                .isActive(true)
                .build();
    }

    @Test
    void testAddItemToCart_NewItem() {
        AddToCartRequest request = AddToCartRequest.builder()
                .productId(productId)
                .quantity(2)
                .build();

        when(productRepository.findById(productId)).thenReturn(Optional.of(product));
        when(cartRepository.findByUserId(userId)).thenReturn(Optional.of(cart));
        when(cartItemRepository.findByCart_CartIdAndProduct_Id(1, productId)).thenReturn(Optional.empty());

        CartItem savedItem = CartItem.builder()
                .cartItemId(10)
                .cart(cart)
                .product(product)
                .quantity(2)
                .build();

        when(cartItemRepository.save(any(CartItem.class))).thenReturn(savedItem);
        when(cartItemRepository.findByCart_CartId(1)).thenReturn(List.of(savedItem));

        CartResponse response = cartService.addItemToCart(userId, request);

        assertNotNull(response);
        assertEquals(1, response.getItems().size());
        assertEquals(2, response.getTotalItems());
        assertEquals(new BigDecimal("3000.0"), response.getTotalAmount());
    }

    @Test
    void testUpdateItemQuantity_Success() {
        CartItem existingItem = CartItem.builder()
                .cartItemId(10)
                .cart(cart)
                .product(product)
                .quantity(2)
                .build();

        when(cartRepository.findByUserId(userId)).thenReturn(Optional.of(cart));
        when(cartItemRepository.findByCart_CartIdAndProduct_Id(1, productId)).thenReturn(Optional.of(existingItem));
        when(cartItemRepository.findByCart_CartId(1)).thenReturn(List.of(existingItem));

        CartResponse response = cartService.updateItemQuantity(userId, productId, 5);

        assertEquals(5, existingItem.getQuantity());
        verify(cartItemRepository, times(1)).save(existingItem);
    }

    @Test
    void testRemoveItemFromCart_Success() {
        CartItem existingItem = CartItem.builder()
                .cartItemId(10)
                .cart(cart)
                .product(product)
                .quantity(2)
                .build();

        when(cartRepository.findByUserId(userId)).thenReturn(Optional.of(cart));
        when(cartItemRepository.findByCart_CartIdAndProduct_Id(1, productId)).thenReturn(Optional.of(existingItem));
        when(cartItemRepository.findByCart_CartId(1)).thenReturn(List.of());

        CartResponse response = cartService.removeItemFromCart(userId, productId);

        assertNotNull(response);
        assertEquals(0, response.getItems().size());
        verify(cartItemRepository, times(1)).delete(existingItem);
    }

    @Test
    void testClearCart_Success() {
        when(cartRepository.findByUserId(userId)).thenReturn(Optional.of(cart));

        cartService.clearCart(userId);

        verify(cartItemRepository, times(1)).deleteByCart_CartId(1);
    }
}
