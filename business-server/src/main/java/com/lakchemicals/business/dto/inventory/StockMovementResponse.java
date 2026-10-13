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
public class StockMovementResponse {

    @JsonProperty("movement_id")
    private Integer movementId;

    @JsonProperty("product_id")
    private UUID productId;

    @JsonProperty("product_name")
    private String productName;

    @JsonProperty("movement_type")
    private String movementType;

    private Integer quantity;
    private String reference;

    @JsonProperty("movement_date")
    private LocalDateTime movementDate;

    @JsonProperty("created_by")
    private String createdBy;
}
