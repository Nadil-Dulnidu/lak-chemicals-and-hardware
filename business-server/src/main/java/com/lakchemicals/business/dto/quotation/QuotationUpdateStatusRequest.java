package com.lakchemicals.business.dto.quotation;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.QuotationStatus;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class QuotationUpdateStatusRequest {

    @NotNull(message = "Status is required")
    private QuotationStatus status;

    @DecimalMin(value = "0.00", message = "Discount amount cannot be negative")
    @JsonProperty("discount_amount")
    private BigDecimal discountAmount;
}
