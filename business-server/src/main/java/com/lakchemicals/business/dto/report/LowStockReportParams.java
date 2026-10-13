package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class LowStockReportParams {

    private String category;

    @Min(value = 0, message = "Threshold percentage cannot be negative")
    @Max(value = 100, message = "Threshold percentage cannot exceed 100")
    @JsonProperty("threshold_percentage")
    @Builder.Default
    private Integer thresholdPercentage = 20;
}
