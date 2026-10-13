package com.lakchemicals.business.dto.order;

import com.lakchemicals.business.constants.OrderStatus;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class OrderUpdateStatusRequest {

    @NotNull(message = "Order status is required")
    private OrderStatus status;
}
