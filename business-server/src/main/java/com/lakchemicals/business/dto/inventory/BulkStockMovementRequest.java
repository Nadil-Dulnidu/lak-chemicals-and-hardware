package com.lakchemicals.business.dto.inventory;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.Size;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class BulkStockMovementRequest {

    @NotEmpty(message = "At least one movement is required")
    @Size(max = 100, message = "Maximum 100 movements allowed per bulk operation")
    @Valid
    private List<StockMovementCreateRequest> movements;
}
