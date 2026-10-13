package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class RunReportParams {

    @JsonProperty("start_date")
    private LocalDateTime startDate;

    @JsonProperty("end_date")
    private LocalDateTime endDate;

    private String category;

    @JsonProperty("product_id")
    private UUID productId;

    @JsonProperty("group_by")
    private String groupBy;

    @JsonProperty("top_n")
    private Integer topN;

    @JsonProperty("threshold_percentage")
    private Integer thresholdPercentage;

    @JsonProperty("low_stock_only")
    private Boolean lowStockOnly;
}
