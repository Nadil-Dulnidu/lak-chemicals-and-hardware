package com.lakchemicals.business.dto.inventory;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ReorderAlertResponse {

    @JsonProperty("product_id")
    private UUID productId;

    @JsonProperty("product_name")
    private String productName;

    @JsonProperty("current_stock")
    private Integer currentStock;

    @JsonProperty("reorder_threshold")
    private Integer reorderThreshold;

    @JsonProperty("quantity_needed")
    private Integer quantityNeeded;

    private String priority;
}
