package com.lakchemicals.business.dto.order;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderCreateFromQuotationRequest {

    @NotNull(message = "Quotation ID is required")
    @JsonProperty("quotation_id")
    private Integer quotationId;

    @JsonProperty("payment_method")
    private String paymentMethod;

    private String notes;

    @JsonProperty("customer_name")
    private String customerName;

    private String phone;
    private String address;
    private String city;
}
