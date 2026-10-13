package com.lakchemicals.business.dto.supplier;

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
public class SupplierListResponse {

    private List<SupplierResponse> suppliers;
    private Long total;
    private Integer skip;
    private Integer limit;

    @JsonProperty("has_more")
    private Boolean hasMore;
}
