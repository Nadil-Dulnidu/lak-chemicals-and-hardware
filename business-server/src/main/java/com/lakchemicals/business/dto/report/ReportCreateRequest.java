package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.ReportType;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.Map;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReportCreateRequest {

    @NotBlank(message = "Report name is required")
    @JsonProperty("report_name")
    private String reportName;

    @NotNull(message = "Report type is required")
    @JsonProperty("report_type")
    private ReportType reportType;

    private Map<String, Object> parameters;

    private String description;
}
