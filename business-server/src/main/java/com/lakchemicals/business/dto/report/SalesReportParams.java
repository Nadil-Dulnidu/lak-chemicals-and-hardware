package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotNull;
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
public class SalesReportParams {

    @NotNull(message = "Start date is required")
    @JsonProperty("start_date")
    private LocalDateTime startDate;

    @NotNull(message = "End date is required")
    @JsonProperty("end_date")
    private LocalDateTime endDate;

    @JsonProperty("product_id")
    private UUID productId;

    private String category;

    @JsonProperty("group_by")
    @Builder.Default
    private String groupBy = "day";
}
