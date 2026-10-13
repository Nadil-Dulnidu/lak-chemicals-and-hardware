package com.lakchemicals.business.dto.report;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ProductPerformanceItem {

    @JsonProperty("product_id")
    private UUID productId;

    @JsonProperty("product_name")
    private String productName;

    private String category;

    @JsonProperty("total_quantity_sold")
    private Integer totalQuantitySold;

    @JsonProperty("total_revenue")
    private BigDecimal totalRevenue;

    @JsonProperty("number_of_orders")
    private Integer numberOfOrders;

    @JsonProperty("average_order_quantity")
    private BigDecimal averageOrderQuantity;
}
