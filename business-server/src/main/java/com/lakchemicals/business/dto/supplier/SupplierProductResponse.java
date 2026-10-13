package com.lakchemicals.business.dto.supplier;

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
public class SupplierProductResponse {

    @JsonProperty("supplier_id")
    private UUID supplierId;

    @JsonProperty("product_id")
    private UUID productId;

    @JsonProperty("supply_price")
    private Double supplyPrice;

    @JsonProperty("created_at")
    private LocalDateTime createdAt;

    @JsonProperty("last_supplied_date")
    private LocalDateTime lastSuppliedDate;
}
