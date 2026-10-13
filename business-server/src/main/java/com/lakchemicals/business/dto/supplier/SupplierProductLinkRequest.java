package com.lakchemicals.business.dto.supplier;

import com.fasterxml.jackson.annotation.JsonProperty;
import jakarta.validation.constraints.DecimalMin;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class SupplierProductLinkRequest {

    @NotNull(message = "Product ID is required")
    @JsonProperty("product_id")
    private UUID productId;

    @DecimalMin(value = "0.01", message = "Supply price must be greater than 0")
    @JsonProperty("supply_price")
    private Double supplyPrice;
}
