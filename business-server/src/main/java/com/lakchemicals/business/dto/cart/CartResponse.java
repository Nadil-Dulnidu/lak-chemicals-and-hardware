package com.lakchemicals.business.dto.cart;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class CartResponse {

    @JsonProperty("cart_id")
    private Integer cartId;

    @JsonProperty("user_id")
    private String userId;

    @Builder.Default
    private List<CartItemResponse> items = new ArrayList<>();

    @JsonProperty("total_items")
    private Integer totalItems;

    @JsonProperty("total_amount")
    private BigDecimal totalAmount;
}
