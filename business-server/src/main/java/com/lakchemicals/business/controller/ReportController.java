package com.lakchemicals.business.controller;

import com.lakchemicals.business.constants.ReportType;
import com.lakchemicals.business.dto.report.*;
import com.lakchemicals.business.security.SecurityUtils;
import com.lakchemicals.business.service.ReportService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

@Slf4j
@RestController
@RequestMapping({"/api/v1/reports", "/reports"})
@Tag(name = "Reports", description = "Report Configuration and Analytics Endpoints")
@PreAuthorize("hasAuthority('ROLE_ADMIN')")
@RequiredArgsConstructor
public class ReportController {

    private final ReportService reportService;

    @PostMapping({"", "/"})
    @Operation(summary = "Save a report configuration")
    public ResponseEntity<ReportResponse> createReport(@Valid @RequestBody ReportCreateRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.status(HttpStatus.CREATED).body(reportService.createReport(userId, request));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get report configuration by ID")
    public ResponseEntity<ReportResponse> getReportById(@PathVariable("id") Integer id) {
        return ResponseEntity.ok(reportService.getReportById(id));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update report configuration")
    public ResponseEntity<ReportResponse> updateReport(
            @PathVariable("id") Integer id,
            @Valid @RequestBody ReportUpdateRequest request
    ) {
        return ResponseEntity.ok(reportService.updateReport(id, request));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete report configuration")
    public ResponseEntity<Void> deleteReport(@PathVariable("id") Integer id) {
        reportService.deleteReport(id);
        return ResponseEntity.noContent().build();
    }

    @GetMapping({"", "/"})
    @Operation(summary = "List saved report configurations")
    public ResponseEntity<ReportListResponse> getReports(
            @RequestParam(value = "report_type", required = false) String reportType,
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit
    ) {
        ReportType type = reportType != null ? ReportType.fromValue(reportType) : null;
        return ResponseEntity.ok(reportService.getAllReports(type, skip, limit));
    }

    @PostMapping("/generate/sales")
    @Operation(summary = "Generate sales report on demand")
    public ResponseEntity<SalesReportData> generateSalesReport(@Valid @RequestBody SalesReportParams params) {
        return ResponseEntity.ok(reportService.generateSalesReport(params));
    }

    @PostMapping("/generate/inventory")
    @Operation(summary = "Generate inventory report on demand")
    public ResponseEntity<InventoryReportData> generateInventoryReport(@Valid @RequestBody InventoryReportParams params) {
        return ResponseEntity.ok(reportService.generateInventoryReport(params));
    }

    @PostMapping("/generate/product-performance")
    @Operation(summary = "Generate product performance report on demand")
    public ResponseEntity<ProductPerformanceData> generateProductPerformanceReport(@Valid @RequestBody ProductPerformanceParams params) {
        return ResponseEntity.ok(reportService.generateProductPerformanceReport(params));
    }

    @PostMapping("/generate/low-stock")
    @Operation(summary = "Generate low stock report on demand")
    public ResponseEntity<LowStockReportData> generateLowStockReport(@Valid @RequestBody LowStockReportParams params) {
        return ResponseEntity.ok(reportService.generateLowStockReport(params));
    }
}
