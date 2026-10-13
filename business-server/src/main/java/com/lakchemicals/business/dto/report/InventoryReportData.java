package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class InventoryReportData {

    @JsonProperty("report_type")
    @Builder.Default
    private String reportType = "INVENTORY";

    @JsonProperty("generated_at")
    private LocalDateTime generatedAt;

    private Map<String, Object> summary;

    @Builder.Default
    private List<InventoryReportItem> items = new ArrayList<>();

    @JsonProperty("low_stock_items")
    @Builder.Default
    private List<InventoryReportItem> lowStockItems = new ArrayList<>();
}
