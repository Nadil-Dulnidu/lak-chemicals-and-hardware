package com.lakchemicals.business.controller;

import com.lakchemicals.business.constants.QuotationStatus;
import com.lakchemicals.business.dto.quotation.*;
import com.lakchemicals.business.security.SecurityUtils;
import com.lakchemicals.business.service.QuotationService;
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

@Slf4j
@RestController
@RequestMapping({"/api/v1/quotations", "/quotations"})
@Tag(name = "Quotations", description = "Quotation Management Endpoints")
@RequiredArgsConstructor
public class QuotationController {

    private final QuotationService quotationService;

    @PostMapping({"", "/"})
    @Operation(summary = "Create a new quotation request")
    public ResponseEntity<QuotationResponse> createQuotation(@Valid @RequestBody QuotationCreateRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        String userEmail = SecurityUtils.getCurrentUserEmail();
        return ResponseEntity.status(HttpStatus.CREATED).body(quotationService.createQuotation(userId, userEmail, request));
    }

    @PostMapping("/from-cart")
    @Operation(summary = "Create a quotation request from existing cart")
    public ResponseEntity<QuotationResponse> createQuotationFromCart(@RequestBody(required = false) QuotationFromCartRequest request) {
        String userId = SecurityUtils.getCurrentUserId();
        String userEmail = SecurityUtils.getCurrentUserEmail();
        return ResponseEntity.status(HttpStatus.CREATED).body(quotationService.createQuotationFromCart(userId, userEmail, request));
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get quotation by ID")
    public ResponseEntity<QuotationResponse> getQuotationById(@PathVariable("id") Integer id) {
        String userId = SecurityUtils.getCurrentUserId();
        boolean isAdmin = SecurityUtils.isAdmin();
        return ResponseEntity.ok(quotationService.getQuotationById(id, userId, isAdmin));
    }

    @GetMapping({"", "/"})
    @Operation(summary = "List quotations (user's quotations or all quotations if admin)")
    public ResponseEntity<QuotationListResponse> getQuotations(
            @RequestParam(value = "status", required = false) String status,
            @RequestParam(value = "start_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startDate,
            @RequestParam(value = "end_date", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endDate,
            @RequestParam(value = "skip", required = false, defaultValue = "0") int skip,
            @RequestParam(value = "limit", required = false, defaultValue = "100") int limit
    ) {
        String userId = SecurityUtils.getCurrentUserId();
        boolean isAdmin = SecurityUtils.isAdmin();

        if (isAdmin) {
            QuotationStatus qStatus = status != null ? QuotationStatus.fromValue(status) : null;
            return ResponseEntity.ok(quotationService.filterQuotations(qStatus, startDate, endDate, skip, limit));
        } else {
            return ResponseEntity.ok(quotationService.getUserQuotations(userId, skip, limit));
        }
    }

    @PatchMapping("/{id}/status")
    @PreAuthorize("hasAuthority('ROLE_ADMIN')")
    @Operation(summary = "Update quotation status (approve or reject with discount)")
    public ResponseEntity<QuotationResponse> updateStatus(
            @PathVariable("id") Integer id,
            @Valid @RequestBody QuotationUpdateStatusRequest request
    ) {
        return ResponseEntity.ok(quotationService.updateQuotationStatus(id, request.getStatus(), request.getDiscountAmount()));
    }

    @DeleteMapping("/{id}")
    @ResponseStatus(HttpStatus.NO_CONTENT)
    @Operation(summary = "Delete a quotation")
    public ResponseEntity<Void> deleteQuotation(@PathVariable("id") Integer id) {
        String userId = SecurityUtils.getCurrentUserId();
        boolean isAdmin = SecurityUtils.isAdmin();
        quotationService.deleteQuotation(id, userId, isAdmin);
        return ResponseEntity.noContent().build();
    }
}
