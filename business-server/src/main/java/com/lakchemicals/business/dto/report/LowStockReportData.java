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
public class LowStockReportData {

    @JsonProperty("report_type")
    @Builder.Default
    private String reportType = "LOW_STOCK";

    @JsonProperty("generated_at")
    private LocalDateTime generatedAt;

    @JsonProperty("threshold_percentage")
    private Integer thresholdPercentage;

    private Map<String, Object> summary;

    @Builder.Default
    private List<LowStockItem> items = new ArrayList<>();
}
