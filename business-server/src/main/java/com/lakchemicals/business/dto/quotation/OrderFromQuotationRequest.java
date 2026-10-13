package com.lakchemicals.business.dto.quotation;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderFromQuotationRequest {

    @JsonProperty("payment_method")
    private String paymentMethod;

    @JsonProperty("customer_name")
    private String customerName;

    private String phone;
    private String address;
    private String city;
    private String notes;
}
