package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiGeneratedReportResponse {

    @JsonProperty("report_type")
    private String reportType;

    @JsonProperty("generated_at")
    private LocalDateTime generatedAt;

    @JsonProperty("raw_data")
    private Object rawData;

    @JsonProperty("ai_analysis")
    private AiReportAnalysisResponse aiAnalysis;
}
