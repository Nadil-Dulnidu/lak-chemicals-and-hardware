package com.lakchemicals.business.dto.order;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.OrderStatus;
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
public class OrderSummaryResponse {

    @JsonProperty("order_id")
    private Integer orderId;

    @JsonProperty("user_id")
    private String userId;

    private OrderStatus status;

    @JsonProperty("total_amount")
    private BigDecimal totalAmount;

    @JsonProperty("order_date")
    private LocalDateTime orderDate;

    @JsonProperty("completed_date")
    private LocalDateTime completedDate;

    @JsonProperty("cart_id")
    private Integer cartId;

    @JsonProperty("quotation_id")
    private Integer quotationId;
}
