package com.lakchemicals.business.dto.inventory;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class StockMovementListResponse {

    private List<StockMovementResponse> movements;
    private Long total;
    private Integer skip;
    private Integer limit;

    @JsonProperty("has_more")
    private Boolean hasMore;
}
