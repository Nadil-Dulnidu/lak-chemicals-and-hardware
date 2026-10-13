package com.lakchemicals.business.controller;

import com.lakchemicals.business.dto.supplier.*;
import com.lakchemicals.business.security.SecurityUtils;
import com.lakchemicals.business.service.SupplierService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@Slf4j
@RestController
@RequestMapping({"/api/v1/suppliers", "/suppliers"})
@Tag(name = "Suppliers", description = "Supplier Management Endpoints")
@PreAuthorize("hasAuthority('ROLE_ADMIN')")
@RequiredArgsConstructor
public class SupplierController {

    private final SupplierService supplierService;

    @PostMapping
    @Operation(summary = "Create a new supplier")
    public ResponseEntity<SupplierResponse> createSupplier(@Valid @RequestBody SupplierCreateRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        SupplierResponse response = supplierService.createSupplier(request, userId);
        return ResponseEntity.status(HttpStatus.CREATED).body(response);
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get supplier by ID")
    public ResponseEntity<SupplierResponse> getSupplierById(@PathVariable("id") UUID id) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(supplierService.getSupplierById(id, userId));
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update supplier by ID")
    public ResponseEntity<SupplierResponse> updateSupplier(
            @PathVariable("id") UUID id,
            @Valid @RequestBody SupplierUpdateRequest request
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(supplierService.updateSupplier(id, request, userId));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete supplier (soft delete)")
    public ResponseEntity<Void> deleteSupplier(@PathVariable("id") UUID id) {
        String userId = SecurityUtils.getCurrentUserId();
        supplierService.deleteSupplier(id, userId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping
    @Operation(summary = "Get all suppliers with pagination and filtering")
    public ResponseEntity<SupplierListResponse> getSuppliers(
            @RequestParam(value = "is_active", required = false, defaultValue = "true") Boolean isActive,
            @RequestParam(value = "search", required = false) String search,
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit
    ) {
        return ResponseEntity.ok(supplierService.filterSuppliers(isActive, search, skip, limit));
    }

    @PostMapping("/{id}/products")
    @Operation(summary = "Link a product to a supplier")
    public ResponseEntity<SupplierProductResponse> linkProduct(
            @PathVariable("id") UUID id,
            @Valid @RequestBody SupplierProductLinkRequest request
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(supplierService.linkProduct(id, request.getProductId(), request.getSupplyPrice(), userId));
    }

    @DeleteMapping("/{id}/products/{product_id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Unlink a product from a supplier")
    public ResponseEntity<Void> unlinkProduct(
            @PathVariable("id") UUID id,
            @PathVariable("product_id") UUID productId
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        supplierService.unlinkProduct(id, productId, userId);
        return ResponseEntity.noContent().build();
    }

    @GetMapping("/{id}/details")
    @Operation(summary = "Get supplier details with products")
    public ResponseEntity<SupplierDetailResponse> getSupplierDetails(@PathVariable("id") UUID id) {
        String userId = SecurityUtils.getCurrentUserId();
        return ResponseEntity.ok(supplierService.getSupplierDetails(id, userId));
    }
}
