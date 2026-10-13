package com.lakchemicals.business.controller;

import com.lakchemicals.business.constants.OrderStatus;
import com.lakchemicals.business.dto.order.*;
import com.lakchemicals.business.security.SecurityUtils;
import com.lakchemicals.business.service.OrderService;
import com.lakchemicals.business.service.SalesService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping({"/api/v1/orders", "/orders"})
@Tag(name = "Orders", description = "Order Management Endpoints")
@RequiredArgsConstructor
public class OrderController {

    private final OrderService orderService;
    private final SalesService salesService;

    @PostMapping("/from-cart")
    @Operation(summary = "Create an order from user's cart")
    public ResponseEntity<OrderResponse> createFromCart(@Valid @RequestBody OrderCreateFromCartRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(orderService.createOrderFromCart(userId, request));
    }

    @PostMapping("/from-quotation")
    @Operation(summary = "Create an order from an approved quotation")
    public ResponseEntity<OrderResponse> createFromQuotation(@Valid @RequestBody OrderCreateFromQuotationRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(orderService.createOrderFromQuotation(userId, request));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get order by ID")
    public ResponseEntity<OrderResponse> getOrderById(@PathVariable("id") Integer id) {
        String userId = SecurityUtils.getCurrentUserId();
        boolean isAdmin = SecurityUtils.isAdmin();
        return ResponseEntity.ok(orderService.getOrderById(id, userId, isAdmin));
    }

    @GetMapping({"", "/"})
    @Operation(summary = "List orders (user's orders or all orders if admin)")
    public ResponseEntity<OrderListResponse> getOrders(
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "start_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam(value = "end_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate,
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        boolean isAdmin = SecurityUtils.isAdmin();

        if (isAdmin) {
            OrderStatus orderStatus = status != null ? OrderStatus.fromValue(status) : null;
            return ResponseEntity.ok(orderService.filterOrders(orderStatus, startDate, endDate, skip, limit));
        } else {
            return ResponseEntity.ok(orderService.getUserOrders(userId, skip, limit));
        }
    }

    @PatchMapping("/{id}/status")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @Operation(summary = "Update order status")
    public ResponseEntity<OrderResponse> updateStatus(
            @PathVariable("id") Integer id,
            @Valid @RequestBody OrderUpdateStatusRequest request
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(orderService.updateOrderStatus(id, request.getStatus(), userId));
    }

    @GetMapping("/sales")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @Operation(summary = "Get sales records with pagination and filtering")
    public ResponseEntity<SalesListResponse> getSales(
            @RequestParam(value = "product_id", required = false) UUID productId,
            @RequestParam(value = "start_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam(value = "end_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate,
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit
    ) {
        return ResponseEntity.ok(salesService.filterSales(productId, startDate, endDate, skip, limit));
    }

    @GetMapping("/sales/summary")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @Operation(summary = "Get sales revenue and quantity summary")
    public ResponseEntity<SalesSummaryResponse> getSalesSummary(
            @RequestParam(value = "start_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam(value = "end_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate
    ) {
        return ResponseEntity.ok(salesService.getSalesSummary(startDate, endDate));
    }
}
