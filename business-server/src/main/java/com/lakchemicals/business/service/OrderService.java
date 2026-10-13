package com.lakchemicals.business.service;

import com.lakchemicals.business.constants.MovementType;
import com.lakchemicals.business.constants.OrderStatus;
import com.lakchemicals.business.constants.PaymentStatus;
import com.lakchemicals.business.dto.order.*;
import com.lakchemicals.business.entity.*;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.exception.ForbiddenException;
import com.lakchemicals.business.exception.ResourceNotFoundException;
import com.lakchemicals.business.repository.*;
import jakarta.persistence.criteria.Predicate;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Slf4j
@Service
@RequiredArgsConstructor
public class OrderService {

    private final OrderRepository orderRepository;
    private final OrderProductRepository orderProductRepository;
    private final CartRepository cartRepository;
    private final CartItemRepository cartItemRepository;
    private final QuotationRepository quotationRepository;
    private final ProductRepository productRepository;
    private final StockMovementRepository stockMovementRepository;
    private final SaleRepository saleRepository;

    @Transactional
    public OrderResponse createOrderFromCart(String userId, OrderCreateFromCartRequest request) {
        log.info("Creating order from cart {} for user {}", request.getCartId(), userId);

        Cart cart = cartRepository.findById(request.getCartId())
                .orElseThrow(() -> new ResourceNotFoundException("Cart not found with id: " + request.getCartId()));

        if (!cart.getUserId().equals(userId)) {
            throw new ForbiddenException("Cannot create order from another user's cart");
        }

        List<CartItem> cartItems = cartItemRepository.findByCart_CartId(cart.getCartId());
        if (cartItems.isEmpty()) {
            throw new BadRequestException("Cart is empty");
        }

        BigDecimal totalAmount = BigDecimal.ZERO;

        // Check stock availability
        for (CartItem item : cartItems) {
            Product p = item.getProduct();
            if (p.getStockQty() < item.getQuantity()) {
                throw new BadRequestException("Insufficient stock for product '" + p.getName() + "'. Available: " + p.getStockQty());
            }
            BigDecimal unitPrice = BigDecimal.valueOf(p.getPrice());
            totalAmount = totalAmount.add(unitPrice.multiply(BigDecimal.valueOf(item.getQuantity())));
        }

        Order order = Order.builder()
                .userId(userId)
                .cartId(cart.getCartId())
                .status(OrderStatus.PENDING)
                .totalAmount(totalAmount)
                .paymentMethod(request.getPaymentMethod())
                .paymentStatus(PaymentStatus.UNPAID)
                .notes(request.getNotes())
                .customerName(request.getCustomerName())
                .phone(request.getPhone())
                .address(request.getAddress())
                .city(request.getCity())
                .orderDate(LocalDateTime.now())
                .build();

        Order savedOrder = orderRepository.save(order);

        // Create OrderProduct snapshots and update stock
        List<OrderProduct> orderProducts = new ArrayList<>();
        for (CartItem item : cartItems) {
            Product p = item.getProduct();
            BigDecimal unitPrice = BigDecimal.valueOf(p.getPrice());
            BigDecimal subtotal = unitPrice.multiply(BigDecimal.valueOf(item.getQuantity()));

            OrderProduct op = OrderProduct.builder()
                    .order(savedOrder)
                    .product(p)
                    .quantity(item.getQuantity())
                    .unitPrice(unitPrice)
                    .subtotal(subtotal)
                    .build();
            orderProducts.add(orderProductRepository.save(op));

            // Reduce stock
            p.setStockQty(p.getStockQty() - item.getQuantity());
            productRepository.save(p);

            // Record movement
            StockMovement movement = StockMovement.builder()
                    .product(p)
                    .movementType(MovementType.OUT)
                    .quantity(item.getQuantity())
                    .reference("Order #" + savedOrder.getOrderId())
                    .movementDate(LocalDateTime.now())
                    .createdBy(userId)
                    .build();
            stockMovementRepository.save(movement);
        }

        savedOrder.setOrderProducts(orderProducts);

        // Clear cart
        cartItemRepository.deleteByCart_CartId(cart.getCartId());
        cart.getCartItems().clear();

        return mapToResponse(savedOrder);
    }

    @Transactional
    public OrderResponse createOrderFromQuotation(String userId, OrderCreateFromQuotationRequest request) {
        log.info("Creating order from quotation {} for user {}", request.getQuotationId(), userId);

        Quotation quotation = quotationRepository.findById(request.getQuotationId())
                .orElseThrow(() -> new ResourceNotFoundException("Quotation not found with id: " + request.getQuotationId()));

        if (!quotation.getUserId().equals(userId)) {
            throw new ForbiddenException("Cannot create order from another user's quotation");
        }

        if (quotation.getStatus() != com.lakchemicals.business.constants.QuotationStatus.APPROVED) {
            throw new BadRequestException("Order can only be created from an APPROVED quotation. Current status: " + quotation.getStatus());
        }

        BigDecimal netAmount = quotation.getTotalAmount().subtract(
                quotation.getDiscountAmount() != null ? quotation.getDiscountAmount() : BigDecimal.ZERO
        );

        Order order = Order.builder()
                .userId(userId)
                .quotationId(quotation.getQuotationId())
                .status(OrderStatus.PENDING)
                .totalAmount(netAmount)
                .paymentMethod(request.getPaymentMethod())
                .paymentStatus(PaymentStatus.UNPAID)
                .notes(request.getNotes())
                .customerName(request.getCustomerName())
                .phone(request.getPhone())
                .address(request.getAddress())
                .city(request.getCity())
                .orderDate(LocalDateTime.now())
                .build();

        Order savedOrder = orderRepository.save(order);

        List<OrderProduct> orderProducts = new ArrayList<>();
        for (QuotationItem qi : quotation.getQuotationItems()) {
            Product p = qi.getProduct();
            OrderProduct op = OrderProduct.builder()
                    .order(savedOrder)
                    .product(p)
                    .quantity(qi.getQuantity())
                    .unitPrice(qi.getUnitPrice())
                    .subtotal(qi.getSubtotal())
                    .build();
            orderProducts.add(orderProductRepository.save(op));

            // Reduce stock
            p.setStockQty(Math.max(0, p.getStockQty() - qi.getQuantity()));
            productRepository.save(p);

            // Record movement
            StockMovement movement = StockMovement.builder()
                    .product(p)
                    .movementType(MovementType.OUT)
                    .quantity(qi.getQuantity())
                    .reference("Order #" + savedOrder.getOrderId() + " (Quotation #" + quotation.getQuotationId() + ")")
                    .movementDate(LocalDateTime.now())
                    .createdBy(userId)
                    .build();
            stockMovementRepository.save(movement);
        }

        savedOrder.setOrderProducts(orderProducts);
        return mapToResponse(savedOrder);
    }

    @Transactional(readOnly = true)
    public OrderResponse getOrderById(Integer orderId, String userId, boolean isAdmin) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + orderId));

        if (!isAdmin && !order.getUserId().equals(userId)) {
            throw new ForbiddenException("Access denied to order: " + orderId);
        }

        return mapToResponse(order);
    }

    @Transactional(readOnly = true)
    public OrderResponse getOrderByIdAdmin(Integer orderId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + orderId));
        return mapToResponse(order);
    }

    @Transactional(readOnly = true)
    public OrderListResponse getUserOrders(String userId, int skip, int limit) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "orderDate"));

        Page<Order> orderPage = orderRepository.findByUserId(userId, pageable);
        List<OrderResponse> dtos = orderPage.getContent().stream().map(this::mapToResponse).toList();

        return OrderListResponse.builder()
                .orders(dtos)
                .total(orderPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(orderPage.hasNext())
                .build();
    }

    @Transactional(readOnly = true)
    public OrderListResponse filterOrders(
            OrderStatus status,
            LocalDateTime startDate,
            LocalDateTime endDate,
            int skip,
            int limit
    ) {
        int page = skip / limit;
        Pageable pageable = PageRequest.of(page, limit, Sort.by(Sort.Direction.DESC, "orderDate"));

        Specification<Order> spec = (root, query, cb) -> {
            List<Predicate> predicates = new ArrayList<>();
            if (status != null) {
                predicates.add(cb.equal(root.get("status"), status));
            }
            if (startDate != null) {
                predicates.add(cb.greaterThanOrEqualTo(root.get("orderDate"), startDate));
            }
            if (endDate != null) {
                predicates.add(cb.lessThanOrEqualTo(root.get("orderDate"), endDate));
            }
            return cb.and(predicates.toArray(new Predicate[0]));
        };

        Page<Order> orderPage = orderRepository.findAll(spec, pageable);
        List<OrderResponse> dtos = orderPage.getContent().stream().map(this::mapToResponse).toList();

        return OrderListResponse.builder()
                .orders(dtos)
                .total(orderPage.getTotalElements())
                .skip(skip)
                .limit(limit)
                .hasMore(orderPage.hasNext())
                .build();
    }

    @Transactional
    public OrderResponse updateOrderStatus(Integer orderId, OrderStatus newStatus, String userId) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + orderId));

        order.setStatus(newStatus);
        if (newStatus == OrderStatus.DELIVERED) {
            order.setCompletedDate(LocalDateTime.now());

            // Create sales records if not already created
            List<Sale> existingSales = saleRepository.findByOrder_OrderId(orderId);
            if (existingSales.isEmpty()) {
                for (OrderProduct op : order.getOrderProducts()) {
                    Sale sale = Sale.builder()
                            .order(order)
                            .product(op.getProduct())
                            .quantity(op.getQuantity())
                            .revenue(op.getSubtotal())
                            .saleDate(LocalDateTime.now())
                            .build();
                    saleRepository.save(sale);
                }
            }
        } else if (newStatus == OrderStatus.CANCELLED) {
            order.setCancelledDate(LocalDateTime.now());
        }

        Order saved = orderRepository.save(order);
        return mapToResponse(saved);
    }

    @Transactional
    public OrderResponse updatePaymentStatus(Integer orderId, PaymentStatus paymentStatus) {
        Order order = orderRepository.findById(orderId)
                .orElseThrow(() -> new ResourceNotFoundException("Order not found with id: " + orderId));

        order.setPaymentStatus(paymentStatus);
        return mapToResponse(orderRepository.save(order));
    }

    public OrderResponse mapToResponse(Order order) {
        List<OrderProductResponse> items = order.getOrderProducts() != null ?
                order.getOrderProducts().stream()
                        .filter(java.util.Objects::nonNull)
                        .map(op -> OrderProductResponse.builder()
                                .id(op.getId())
                                .productId(op.getProduct() != null ? op.getProduct().getId() : null)
                                .productName(op.getProduct() != null ? op.getProduct().getName() : null)
                                .quantity(op.getQuantity())
                                .unitPrice(op.getUnitPrice())
                                .subtotal(op.getSubtotal())
                                .build()
                        ).toList() : new ArrayList<>();

        return OrderResponse.builder()
                .orderId(order.getOrderId())
                .userId(order.getUserId())
                .status(order.getStatus())
                .totalAmount(order.getTotalAmount())
                .paymentMethod(order.getPaymentMethod())
                .paymentStatus(order.getPaymentStatus())
                .orderDate(order.getOrderDate())
                .completedDate(order.getCompletedDate())
                .cancelledDate(order.getCancelledDate())
                .notes(order.getNotes())
                .cartId(order.getCartId())
                .quotationId(order.getQuotationId())
                .customerName(order.getCustomerName())
                .phone(order.getPhone())
                .address(order.getAddress())
                .city(order.getCity())
                .items(items)
                .build();
    }
}
