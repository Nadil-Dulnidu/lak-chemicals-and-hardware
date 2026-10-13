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
public class LowStockItem {

    @JsonProperty("product_id")
    private UUID productId;

    @JsonProperty("product_name")
    private String productName;

    private String category;

    @JsonProperty("current_stock")
    private Integer currentStock;

    @JsonProperty("reorder_level")
    private Integer reorderLevel;

    @JsonProperty("stock_percentage")
    private BigDecimal stockPercentage;

    @JsonProperty("recommended_order_quantity")
    private Integer recommendedOrderQuantity;
}
