package com.lakchemicals.business;

import com.lakchemicals.business.constants.OrderStatus;
import com.lakchemicals.business.constants.PaymentStatus;
import com.lakchemicals.business.constants.QuotationStatus;
import com.lakchemicals.business.dto.order.*;
import com.lakchemicals.business.entity.*;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.repository.*;
import com.lakchemicals.business.service.OrderService;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class OrderServiceTest {

    @Mock
    private OrderRepository orderRepository;

    @Mock
    private OrderProductRepository orderProductRepository;

    @Mock
    private CartRepository cartRepository;

    @Mock
    private CartItemRepository cartItemRepository;

    @Mock
    private QuotationRepository quotationRepository;

    @Mock
    private ProductRepository productRepository;

    @Mock
    private StockMovementRepository stockMovementRepository;

    @Mock
    private SaleRepository saleRepository;

    @InjectMocks
    private OrderService orderService;

    private String userId = "user_456";
    private Product product;
    private Cart cart;
    private CartItem cartItem;

    @BeforeEach
    void setUp() {
        product = Product.builder()
                .id(UUID.randomUUID())
                .name("Dulux Emulsion")
                .price(4200.0)
                .stockQty(15)
                .isActive(true)
                .build();

        cart = Cart.builder()
                .cartId(1)
                .userId(userId)
                .cartItems(new ArrayList<>())
                .build();

        cartItem = CartItem.builder()
                .cartItemId(5)
                .cart(cart)
                .product(product)
                .quantity(2)
                .build();
    }

    @Test
    void testCreateOrderFromCart_Success() {
        OrderCreateFromCartRequest request = OrderCreateFromCartRequest.builder()
                .cartId(1)
                .customerName("John Doe")
                .phone("0771234567")
                .address("123 Main St")
                .city("Colombo")
                .paymentMethod("card")
                .build();

        when(cartRepository.findById(1)).thenReturn(Optional.of(cart));
        when(cartItemRepository.findByCart_CartId(1)).thenReturn(List.of(cartItem));

        Order savedOrder = Order.builder()
                .orderId(101)
                .userId(userId)
                .cartId(1)
                .status(OrderStatus.PENDING)
                .totalAmount(BigDecimal.valueOf(8400.0))
                .paymentStatus(PaymentStatus.UNPAID)
                .customerName("John Doe")
                .orderDate(LocalDateTime.now())
                .build();

        when(orderRepository.save(any(Order.class))).thenReturn(savedOrder);
        when(orderProductRepository.save(any(OrderProduct.class))).thenAnswer(invocation -> invocation.getArgument(0));

        OrderResponse response = orderService.createOrderFromCart(userId, request);

        assertNotNull(response);
        assertEquals(101, response.getOrderId());
        assertEquals(OrderStatus.PENDING, response.getStatus());
        assertEquals(13, product.getStockQty()); // Reduced by 2
        verify(productRepository, times(1)).save(product);
        verify(stockMovementRepository, times(1)).save(any(StockMovement.class));
        verify(cartItemRepository, times(1)).deleteByCart_CartId(1);
    }

    @Test
    void testCreateOrderFromCart_InsufficientStock_ThrowsBadRequest() {
        product.setStockQty(1); // Less than 2

        OrderCreateFromCartRequest request = OrderCreateFromCartRequest.builder()
                .cartId(1)
                .build();

        when(cartRepository.findById(1)).thenReturn(Optional.of(cart));
        when(cartItemRepository.findByCart_CartId(1)).thenReturn(List.of(cartItem));

        assertThrows(BadRequestException.class, () -> orderService.createOrderFromCart(userId, request));
    }

    @Test
    void testCreateOrderFromQuotation_Success() {
        Quotation quotation = Quotation.builder()
                .quotationId(20)
                .userId(userId)
                .status(QuotationStatus.APPROVED)
                .totalAmount(BigDecimal.valueOf(5000))
                .discountAmount(BigDecimal.valueOf(500))
                .quotationItems(new ArrayList<>())
                .build();

        QuotationItem qi = QuotationItem.builder()
                .quotationItemId(1)
                .quotation(quotation)
                .product(product)
                .quantity(1)
                .unitPrice(BigDecimal.valueOf(5000))
                .subtotal(BigDecimal.valueOf(5000))
                .build();
        quotation.getQuotationItems().add(qi);

        OrderCreateFromQuotationRequest request = OrderCreateFromQuotationRequest.builder()
                .quotationId(20)
                .customerName("Jane Doe")
                .build();

        when(quotationRepository.findById(20)).thenReturn(Optional.of(quotation));

        Order savedOrder = Order.builder()
                .orderId(102)
                .userId(userId)
                .quotationId(20)
                .status(OrderStatus.PENDING)
                .totalAmount(BigDecimal.valueOf(4500))
                .orderDate(LocalDateTime.now())
                .build();

        when(orderRepository.save(any(Order.class))).thenReturn(savedOrder);
        when(orderProductRepository.save(any(OrderProduct.class))).thenAnswer(invocation -> invocation.getArgument(0));

        OrderResponse response = orderService.createOrderFromQuotation(userId, request);

        assertNotNull(response);
        assertEquals(102, response.getOrderId());
        verify(productRepository, times(1)).save(product);
    }

    @Test
    void testUpdateOrderStatus_Delivered_CreatesSale() {
        Order order = Order.builder()
                .orderId(101)
                .userId(userId)
                .status(OrderStatus.SHIPPED)
                .totalAmount(BigDecimal.valueOf(4200))
                .orderProducts(new ArrayList<>())
                .build();

        OrderProduct op = OrderProduct.builder()
                .id(1)
                .order(order)
                .product(product)
                .quantity(1)
                .unitPrice(BigDecimal.valueOf(4200))
                .subtotal(BigDecimal.valueOf(4200))
                .build();
        order.getOrderProducts().add(op);

        when(orderRepository.findById(101)).thenReturn(Optional.of(order));
        when(orderRepository.save(any(Order.class))).thenAnswer(invocation -> invocation.getArgument(0));
        when(saleRepository.findByOrder_OrderId(101)).thenReturn(List.of());

        OrderResponse response = orderService.updateOrderStatus(101, OrderStatus.DELIVERED, "admin");

        assertEquals(OrderStatus.DELIVERED, response.getStatus());
        assertNotNull(order.getCompletedDate());
        verify(saleRepository, times(1)).save(any(Sale.class));
    }
}
