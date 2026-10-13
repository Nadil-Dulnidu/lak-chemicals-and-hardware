package com.lakchemicals.business.dto.payment;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PaymentConfirmResponse {

    private String message;

    @JsonProperty("order_id")
    private Integer orderId;

    @JsonProperty("payment_status")
    private String paymentStatus;
}
