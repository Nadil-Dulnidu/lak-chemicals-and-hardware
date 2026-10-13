package com.lakchemicals.business.dto.quotation;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.QuotationStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class QuotationSummaryResponse {

    @JsonProperty("quotation_id")
    private Integer quotationId;

    @JsonProperty("user_id")
    private String userId;

    private QuotationStatus status;

    @JsonProperty("total_amount")
    private BigDecimal totalAmount;

    @JsonProperty("total_items")
    private Integer totalItems;

    @JsonProperty("created_at")
    private LocalDateTime createdAt;
}
