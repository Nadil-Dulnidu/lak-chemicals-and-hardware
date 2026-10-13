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
public class SalesReportData {

    @JsonProperty("report_type")
    @Builder.Default
    private String reportType = "SALES";

    @JsonProperty("start_date")
    private LocalDateTime startDate;

    @JsonProperty("end_date")
    private LocalDateTime endDate;

    private Map<String, Object> summary;

    @Builder.Default
    private List<SalesReportItem> items = new ArrayList<>();

    @JsonProperty("product_breakdown")
    private List<Map<String, Object>> productBreakdown;

    @JsonProperty("category_breakdown")
    private List<Map<String, Object>> categoryBreakdown;
}
