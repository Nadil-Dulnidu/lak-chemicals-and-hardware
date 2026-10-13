package com.lakchemicals.business.dto.order;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SaleResponse {

    @JsonProperty("sale_id")
    private Integer saleId;

    @JsonProperty("order_id")
    private Integer orderId;

    @JsonProperty("product_id")
    private UUID productId;

    @JsonProperty("product_name")
    private String productName;

    private Integer quantity;
    private BigDecimal revenue;

    @JsonProperty("sale_date")
    private LocalDateTime saleDate;
}
