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
public class PaymentSessionResponse {

    @JsonProperty("checkout_url")
    private String checkoutUrl;

    @JsonProperty("session_id")
    private String sessionId;
}
