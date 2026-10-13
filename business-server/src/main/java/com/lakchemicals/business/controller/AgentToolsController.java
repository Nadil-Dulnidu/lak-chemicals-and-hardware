package com.lakchemicals.business.controller;

import com.lakchemicals.business.dto.cart.AgentCartItemsRequest;
import com.lakchemicals.business.dto.cart.CartResponse;
import com.lakchemicals.business.dto.product.ProductListResponse;
import com.lakchemicals.business.dto.report.*;
import com.lakchemicals.business.service.CartService;
import com.lakchemicals.business.service.ProductService;
import com.lakchemicals.business.service.ReportService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping({"/api/v1/tools", "/api/v1/agents", "/tools", "/agents"})
@Tag(name = "Agent Tools", description = "Endpoints for AI Multi-Agent Tools")
@RequiredArgsConstructor
public class AgentToolsController {

    private final ReportService reportService;
    private final ProductService productService;
    private final CartService cartService;

    @PostMapping("/sales")
    @Operation(summary = "Generate sales report for AI agent")
    public ResponseEntity<SalesReportData> generateSalesReport(@Valid @RequestBody SalesReportParams params) {
        log.info("Agent requesting sales report from {} to {}", params.getStartDate(), params.getEndDate());
        return ResponseEntity.ok(reportService.generateSalesReport(params));
    }

    @PostMapping("/inventory")
    @Operation(summary = "Generate inventory report for AI agent")
    public ResponseEntity<InventoryReportData> generateInventoryReport(@Valid @RequestBody InventoryReportParams params) {
        log.info("Agent requesting inventory report (category: {})", params.getCategory());
        return ResponseEntity.ok(reportService.generateInventoryReport(params));
    }

    @PostMapping("/product-performance")
    @Operation(summary = "Generate product performance report for AI agent")
    public ResponseEntity<ProductPerformanceData> generateProductPerformanceReport(@Valid @RequestBody ProductPerformanceParams params) {
        log.info("Agent requesting product performance report");
        return ResponseEntity.ok(reportService.generateProductPerformanceReport(params));
    }

    @GetMapping("/products")
    @Operation(summary = "Get product list with pagination for AI agent")
    public ResponseEntity<ProductListResponse> getProducts(
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit,
            @RequestParam(value = "include_inactive", required = false, defaultValue = "false") boolean includeInactive
    ) {
        return ResponseEntity.ok(productService.getAllProducts(skip, limit, includeInactive, "agent"));
    }

    @PostMapping("/add-to-cart")
    @Operation(summary = "Add items to cart on behalf of user by AI agent")
    public ResponseEntity<CartResponse> addToCart(@Valid @RequestBody AgentCartItemsRequest request) {
        CartResponse lastResponse = null;
        for (var item : request.getItems()) {
            lastResponse = cartService.addItemToCart(request.getUserId(), item);
        }
        return ResponseEntity.status(HttpStatus.CREATED).body(lastResponse);
    }
}
