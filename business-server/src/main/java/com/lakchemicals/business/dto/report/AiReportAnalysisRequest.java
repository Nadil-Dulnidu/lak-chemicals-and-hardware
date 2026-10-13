package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AiReportAnalysisRequest {

    @JsonProperty("report_type")
    private String reportType;

    private Object data;

    private Map<String, Object> metadata;
}
