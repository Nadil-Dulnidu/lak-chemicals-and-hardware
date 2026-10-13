package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductPerformanceParams {

    @NotNull(message = "Start date is required")
    @JsonProperty("start_date")
    private LocalDateTime startDate;

    @NotNull(message = "End date is required")
    @JsonProperty("end_date")
    private LocalDateTime endDate;

    private String category;

    @Min(value = 1, message = "top_n must be at least 1")
    @Max(value = 100, message = "top_n must be at most 100")
    @JsonProperty("top_n")
    @Builder.Default
    private Integer topN = 10;
}
