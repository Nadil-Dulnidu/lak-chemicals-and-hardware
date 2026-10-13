package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.ArrayList;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiReportAnalysisResponse {

    @JsonProperty("report_type")
    private String reportType;

    private String summary;

    @Builder.Default
    private List<String> insights = new ArrayList<>();

    @Builder.Default
    private List<String> recommendations = new ArrayList<>();

    @JsonProperty("risk_alerts")
    @Builder.Default
    private List<String> riskAlerts = new ArrayList<>();
}
