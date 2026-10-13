package com.lakchemicals.business.dto.order;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.OrderStatus;
import com.lakchemicals.business.constants.PaymentStatus;
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
public class OrderResponse {

    @JsonProperty("order_id")
    private Integer orderId;

    @JsonProperty("user_id")
    private String userId;

    private OrderStatus status;

    @JsonProperty("total_amount")
    private BigDecimal totalAmount;

    @JsonProperty("payment_method")
    private String paymentMethod;

    @JsonProperty("payment_status")
    private PaymentStatus paymentStatus;

    @JsonProperty("order_date")
    private LocalDateTime orderDate;

    @JsonProperty("completed_date")
    private LocalDateTime completedDate;

    @JsonProperty("cancelled_date")
    private LocalDateTime cancelledDate;

    private String notes;

    @JsonProperty("cart_id")
    private Integer cartId;

    @JsonProperty("quotation_id")
    private Integer quotationId;

    @JsonProperty("customer_name")
    private String customerName;

    private String phone;
    private String address;
    private String city;

    @Builder.Default
    private List<OrderProductResponse> items = new ArrayList<>();
}
