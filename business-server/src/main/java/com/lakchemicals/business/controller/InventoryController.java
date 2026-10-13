package com.lakchemicals.business.controller;

import com.lakchemicals.business.constants.MovementType;
import com.lakchemicals.business.dto.inventory.*;
import com.lakchemicals.business.security.SecurityUtils;
import com.lakchemicals.business.service.InventoryService;
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
import java.util.List;
import java.util.UUID;

@Slf4j
@RestController
@RequestMapping({"/api/v1/inventory", "/inventory"})
@Tag(name = "Inventory", description = "Inventory and Stock Management Endpoints")
@PreAuthorize("hasAuthority('ROLE_ADMIN')")
@RequiredArgsConstructor
public class InventoryController {

    private final InventoryService inventoryService;

    @PostMapping("/movements")
    @Operation(summary = "Record stock movement (IN or OUT)")
    public ResponseEntity<StockMovementResponse> recordMovement(@Valid @RequestBody StockMovementCreateRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(inventoryService.recordStockMovement(request, userId));
    }

    @PostMapping("/movements/bulk")
    @Operation(summary = "Record bulk stock movements")
    public ResponseEntity<List<StockMovementResponse>> recordBulkMovements(@Valid @RequestBody BulkStockMovementRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(inventoryService.recordBulkMovements(request, userId));
    }

    @PostMapping("/adjust")
    @Operation(summary = "Adjust stock quantity to a target level")
    public ResponseEntity<StockMovementResponse> adjustStock(@Valid @RequestBody StockAdjustmentRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(inventoryService.adjustStock(request, userId));
    }

    @GetMapping("/movements")
    @Operation(summary = "Get stock movements with filters and pagination")
    public ResponseEntity<StockMovementListResponse> getMovements(
            @RequestParam(value = "product_id", required = false) UUID productId,
            @RequestParam(value = "movement_type", required = false) String movementType,
            @RequestParam(value = "start_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam(value = "end_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate,
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit
    ) {
        MovementType type = movementType != null ? MovementType.fromValue(movementType) : null;
        return ResponseEntity.ok(inventoryService.getMovements(productId, type, startDate, endDate, skip, limit));
    }

    @GetMapping("/levels/{product_id}")
    @Operation(summary = "Get current stock level for a product")
    public ResponseEntity<InventoryLevelResponse> getInventoryLevel(@PathVariable("product_id") UUID productId) {
        return ResponseEntity.ok(inventoryService.getInventoryLevel(productId));
    }

    @GetMapping("/alerts")
    @Operation(summary = "Get reorder alerts for low stock products")
    public ResponseEntity<List<ReorderAlertResponse>> getReorderAlerts() {
        return ResponseEntity.ok(inventoryService.getReorderAlerts());
    }

    @GetMapping("/summary")
    @Operation(summary = "Get overall inventory summary statistics")
    public ResponseEntity<StockSummaryResponse> getStockSummary() {
        return ResponseEntity.ok(inventoryService.getStockSummary());
    }
}
