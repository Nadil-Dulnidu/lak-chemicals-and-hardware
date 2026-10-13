package com.lakchemicals.business.dto.cart;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CartSummaryResponse {

    @JsonProperty("cart_id")
    private Integer cartId;

    @JsonProperty("user_id")
    private String userId;

    @JsonProperty("total_items")
    private Integer totalItems;

    @JsonProperty("total_amount")
    private BigDecimal totalAmount;
}
