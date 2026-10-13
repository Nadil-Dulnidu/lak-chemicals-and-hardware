package com.lakchemicals.business.dto.inventory;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.lakchemicals.business.constants.MovementType;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotNull;
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
public class StockMovementCreateRequest {

    @NotNull(message = "Product ID is required")
    @JsonProperty("product_id")
    private UUID productId;

    @NotNull(message = "Movement type is required")
    @JsonProperty("movement_type")
    private MovementType movementType;

    @NotNull(message = "Quantity is required")
    @Min(value = 1, message = "Quantity must be greater than 0")
    private Integer quantity;

    private String reference;

    @JsonProperty("movement_date")
    private LocalDateTime movementDate;
}
