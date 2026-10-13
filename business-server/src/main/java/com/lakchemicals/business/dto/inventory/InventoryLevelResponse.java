package com.lakchemicals.business.dto.inventory;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class InventoryLevelResponse {

    @JsonProperty("product_id")
    private UUID productId;

    @JsonProperty("product_name")
    private String productName;

    @JsonProperty("current_stock")
    private Integer currentStock;

    @JsonProperty("total_in")
    private Integer totalIn;

    @JsonProperty("total_out")
    private Integer totalOut;

    @JsonProperty("last_movement_date")
    private LocalDateTime lastMovementDate;
}
