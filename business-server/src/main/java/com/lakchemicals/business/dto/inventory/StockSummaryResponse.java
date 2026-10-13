package com.lakchemicals.business.dto.inventory;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StockSummaryResponse {

    @JsonProperty("total_products")
    private Long totalProducts;

    @JsonProperty("total_stock_value")
    private Double totalStockValue;

    @JsonProperty("low_stock_count")
    private Long lowStockCount;

    @JsonProperty("out_of_stock_count")
    private Long outOfStockCount;

    @JsonProperty("total_movements_today")
    private Long totalMovementsToday;

    @JsonProperty("total_in_today")
    private Long totalInToday;

    @JsonProperty("total_out_today")
    private Long totalOutToday;
}
