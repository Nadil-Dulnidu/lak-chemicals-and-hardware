package com.lakchemicals.business.controller;

import com.lakchemicals.business.dto.report.*;
import com.lakchemicals.business.exception.BadRequestException;
import com.lakchemicals.business.security.SecurityUtils;
import com.lakchemicals.business.service.AiServiceClient;
import com.lakchemicals.business.service.ReportService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping({"/api/v1/reports/generate/ai", "/reports/generate/ai"})
@Tag(name = "AI Reports", description = "Autonomous AI-Driven Report Generation with Gemini Reasoning")
@PreAuthorize("hasAuthority('ROLE_ADMIN')")
@RequiredArgsConstructor
public class AiReportController {

    private final ReportService reportService;
    private final AiServiceClient aiServiceClient;

    @PostMapping("/{type}")
    @Operation(summary = "Generate autonomous AI report with raw data and Gemini executive insights")
    public ResponseEntity<AiGeneratedReportResponse> generateAiReport(
            @PathVariable("type") String type,
            @RequestBody(required = false) Map<String, Object> bodyParams
    ) {
        String adminUser = SecurityUtils.getCurrentUserId();
        log.info("Admin {} requested autonomous AI report for type: {}", adminUser, type);

        Object rawData;
        String normalizedType = type.toLowerCase().trim();
        Map<String, Object> metadata = new HashMap<>();
        metadata.put("requested_by", adminUser);
        metadata.put("timestamp", LocalDateTime.now().toString());

        switch (normalizedType) {
            case "sales": {
                LocalDateTime start = parseDateTime(bodyParams, "start_date", LocalDateTime.now().minusDays(30));
                LocalDateTime end = parseDateTime(bodyParams, "end_date", LocalDateTime.now());
                String cat = bodyParams != null && bodyParams.containsKey("category") ? (String) bodyParams.get("category") : null;
                String groupBy = bodyParams != null && bodyParams.containsKey("group_by") ? (String) bodyParams.get("group_by") : "day";

                SalesReportParams params = SalesReportParams.builder()
                        .startDate(start)
                        .endDate(end)
                        .category(cat)
                        .groupBy(groupBy)
                        .build();
                rawData = reportService.generateSalesReport(params);
                metadata.put("start_date", start.toString());
                metadata.put("end_date", end.toString());
                break;
            }
            case "inventory": {
                String cat = bodyParams != null && bodyParams.containsKey("category") ? (String) bodyParams.get("category") : null;
                Boolean lowStockOnly = bodyParams != null && bodyParams.containsKey("low_stock_only") ? (Boolean) bodyParams.get("low_stock_only") : false;

                InventoryReportParams params = InventoryReportParams.builder()
                        .category(cat)
                        .lowStockOnly(lowStockOnly)
                        .build();
                rawData = reportService.generateInventoryReport(params);
                break;
            }
            case "product-performance": {
                LocalDateTime start = parseDateTime(bodyParams, "start_date", LocalDateTime.now().minusDays(30));
                LocalDateTime end = parseDateTime(bodyParams, "end_date", LocalDateTime.now());
                String cat = bodyParams != null && bodyParams.containsKey("category") ? (String) bodyParams.get("category") : null;
                Integer topN = bodyParams != null && bodyParams.containsKey("top_n") ? ((Number) bodyParams.get("top_n")).intValue() : 10;

                ProductPerformanceParams params = ProductPerformanceParams.builder()
                        .startDate(start)
                        .endDate(end)
                        .category(cat)
                        .topN(topN)
                        .build();
                rawData = reportService.generateProductPerformanceReport(params);
                metadata.put("start_date", start.toString());
                metadata.put("end_date", end.toString());
                break;
            }
            case "low-stock": {
                String cat = bodyParams != null && bodyParams.containsKey("category") ? (String) bodyParams.get("category") : null;
                Integer thresh = bodyParams != null && bodyParams.containsKey("threshold_percentage") ? ((Number) bodyParams.get("threshold_percentage")).intValue() : 20;

                LowStockReportParams params = LowStockReportParams.builder()
                        .category(cat)
                        .thresholdPercentage(thresh)
                        .build();
                rawData = reportService.generateLowStockReport(params);
                break;
            }
            case "sales-prediction": {
                LocalDateTime start = LocalDateTime.now().minusDays(60);
                LocalDateTime end = LocalDateTime.now();

                SalesReportParams params = SalesReportParams.builder()
                        .startDate(start)
                        .endDate(end)
                        .groupBy("week")
                        .build();
                rawData = reportService.generateSalesReport(params);
                metadata.put("prediction_horizon", "30_days");
                break;
            }
            default:
                throw new BadRequestException("Unsupported report type: " + type + ". Must be one of: sales, inventory, product-performance, low-stock, sales-prediction");
        }

        // Call multi-agent-server to generate executive reasoning analysis
        AiReportAnalysisRequest aiReq = AiReportAnalysisRequest.builder()
                .reportType(normalizedType.toUpperCase().replace("-", "_"))
                .data(rawData)
                .metadata(metadata)
                .build();

        AiReportAnalysisResponse aiAnalysis = aiServiceClient.analyzeReport(aiReq);

        AiGeneratedReportResponse response = AiGeneratedReportResponse.builder()
                .reportType(normalizedType)
                .generatedAt(LocalDateTime.now())
                .rawData(rawData)
                .aiAnalysis(aiAnalysis)
                .build();

        return ResponseEntity.ok(response);
    }

    private LocalDateTime parseDateTime(Map<String, Object> params, String key, LocalDateTime defaultVal) {
        if (params == null || !params.containsKey(key) || params.get(key) == null) {
            return defaultVal;
        }
        try {
            return LocalDateTime.parse(params.get(key).toString());
        } catch (Exception e) {
            return defaultVal;
        }
    }
}
