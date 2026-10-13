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
public class ProductPerformanceData {

    @JsonProperty("report_type")
    @Builder.Default
    private String reportType = "PRODUCT_PERFORMANCE";

    @JsonProperty("start_date")
    private LocalDateTime startDate;

    @JsonProperty("end_date")
    private LocalDateTime endDate;

    private Map<String, Object> summary;

    @JsonProperty("top_products")
    @Builder.Default
    private List<ProductPerformanceItem> topProducts = new ArrayList<>();

    @JsonProperty("category_performance")
    @Builder.Default
    private List<Map<String, Object>> categoryPerformance = new ArrayList<>();
}
