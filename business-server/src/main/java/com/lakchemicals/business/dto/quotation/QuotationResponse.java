package com.lakchemicals.business.dto.quotation;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.QuotationStatus;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class QuotationResponse {

    @JsonProperty("quotation_id")
    private Integer quotationId;

    @JsonProperty("user_id")
    private String userId;

    private QuotationStatus status;

    @JsonProperty("total_amount")
    private BigDecimal totalAmount;

    @JsonProperty("discount_amount")
    private BigDecimal discountAmount;

    @JsonProperty("created_at")
    private LocalDateTime createdAt;

    @JsonProperty("updated_at")
    private LocalDateTime updatedAt;

    private String notes;

    @Builder.Default
    private List<QuotationItemResponse> items = new ArrayList<>();
}
